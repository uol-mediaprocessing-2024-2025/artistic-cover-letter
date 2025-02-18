import numpy as np
from PIL import Image,ImageDraw,ImageFont
from matplotlib import pyplot as plt
import cv2

# https://stackoverflow.com/questions/3207219/how-do-i-list-all-files-of-a-directory
from os import listdir
from os.path import isfile, join
onlyfiles = [f for f in listdir("/content/images/") if isfile(join("/content/images/", f))]



def bounded_slice(arr, cx, cy, w, h):
    large_tiled_array = np.tile(arr, (3, 3, 1))
    start_x = cx % arr.shape[1]
    start_y = cy % arr.shape[0]
    return large_tiled_array[start_y:start_y+h, start_x:start_x+w]

# replaced by faster algorithm. Source: Bing AI
def clamped_slice(arr, cx, cy, w, h):
    max_h, max_w = arr.shape[:2]
    # Create an array of coordinates
    y_indices = np.clip(np.arange(cy, cy + h), 0, max_h - 1)
    x_indices = np.clip(np.arange(cx, cx + w), 0, max_w - 1)

    # Use meshgrid to create a grid of coordinates
    y_grid, x_grid = np.meshgrid(y_indices, x_indices, indexing='ij')

    # Use the grid to index into the array
    result = arr[y_grid, x_grid]
    return result


def blend_images(image1, image2):
    R1, G1, B1, A1 = image1[:,:,0], image1[:,:,1], image1[:,:,2], image1[:,:,3] / 255.0
    R2, G2, B2, A2 = image2[:,:,0], image2[:,:,1], image2[:,:,2], image2[:,:,3] / 255.0

    A_result = A2 + A1 * (1 - A2)
    R_result = np.where(A_result > 0, (R2 * A2 + R1 * A1 * (1 - A2)) / A_result, R1)
    G_result = np.where(A_result > 0, (G2 * A2 + G1 * A1 * (1 - A2)) / A_result, G1)
    B_result = np.where(A_result > 0, (B2 * A2 + B1 * A1 * (1 - A2)) / A_result, B1)

    result_image = np.stack([R_result, G_result, B_result, A_result * 255], axis=-1).astype(np.uint8)
    return result_image


class Font:
    def __init__(self,url,font_size):
        self.font = ImageFont.truetype(url,font_size)
        self.font_size = font_size

class Letter:
    def __init__(self,letter,font,x=0,y=0,imgi=0):
        self.letter = letter
        self.font = font
        self.x = x
        self.y = y
        self.imgi = imgi

    def draw(self):

        # get bounding box info
        left, top, right, bottom = self.font.font.getbbox(self.letter)
        w = right - left
        h = self.font.font_size

        # create letter image
        img = Image.new('RGBA', (w, h), color=(0,0,0,0))
        draw = ImageDraw.Draw(img)
        draw.text((0, 0), self.letter, font=self.font.font, fill=(255,255,255,255))
        img_np = np.array(img)

        cx,cy = 100,100   # focus point of the slice
        back_img = Image.open("/content/images/"+onlyfiles[self.imgi % len(onlyfiles)],'r')
        back_img = back_img.convert('RGBA')
        back_img_np = np.array(back_img)

        back_img_np = clamped_slice(back_img_np,cx,cy,w,h)
        # apply alpha
        for r in range(back_img_np.shape[0]):
            for c in range(back_img_np.shape[1]):
                back_img_np[r][c][3] = img_np[r][c][3]

        return back_img_np

    def __str__(self) -> str:
        return f"Letter: {self.letter}, Font: {self.font.font}, X: {self.x}, Y: {self.y}"


class LetterText:
    def __init__(self,text,font,x=0,y=0):
        self.text = text
        self.font = font
        self.x = x
        self.y = y

    def draw(self):
        # get bounding box info
        left, top, right, bottom = self.font.font.getbbox(self.text)
        w = right - left
        h = self.font.font_size

        letters = []
        for i in range(len(self.text)):
            letters.append(Letter(self.text[i],self.font,self.x+i*w,self.y,i))

        img = np.zeros((h,w,4),dtype=np.uint8)
        #draw each letter by copying them onto img using the letter x and y as the offset
        current_x = 0 # Keep track of the current x position
        for letter in letters:
            letter_img = letter.draw()
            letter_w = letter_img.shape[1]
            img[letter.y:letter.y + h, current_x:current_x + letter_w] = letter_img
            current_x += letter_w # Update x for the next letter
        return img


def main():
    font = Font("/content/fonts/impact.ttf",500)
    letter = Letter("D",font,0,0,3)

    # draw the initial text
    text = LetterText("TEST",font,0,0)
    img = text.draw()

    # draw the black and semi-transparent text
    img_black_trans = np.copy(img)
    for r in range(img_black_trans.shape[0]):
        for c in range(img_black_trans.shape[1]):
            img_black_trans[r][c][0] = 0
            img_black_trans[r][c][1] = 0
            img_black_trans[r][c][2] = 0

            old_alpha = img_black_trans[r][c][3]
            img_black_trans[r][c][3] = old_alpha * 0.5
    img_black_trans = cv2.blur(img_black_trans,(15,15),0)

    # draw a blurred version of the text image
    img_blurred = np.copy(img)
    img_blurred = cv2.blur(img_blurred,(30,30))

    final_img = np.zeros((img.shape[0],img.shape[1]*3,4),dtype=np.uint8)
    final_img = blend_images(img_blurred,img_black_trans)
    final_img = blend_images(final_img,img)

    img = final_img

    imgplot = plt.imshow(final_img)
    plt.show()


if __name__ == '__main__':
    main()
