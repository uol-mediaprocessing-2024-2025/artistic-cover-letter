from PIL import Image
import os
import color_schemes
import image_processing
import dead_code
# Needed for some plots, for some reason
#mpl.use('TkAgg')

def main():

    dead_code.generate_video()
    #images = load_images_from_folder("C:/Users/Simon/Pictures/Ukanc")

    #image = image_processing.resizeImageLongest(images[11], 256)

    #color_schemes.plot_colors(color_schemes.get_image_colors(image))

# Loads images from folder and returns image array
# Very useful for prototyping and testing
def load_images_from_folder(folder_path):
    images = []
    for filename in os.listdir(folder_path):
        if filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):  # Add more extensions if needed
            img_path = os.path.join(folder_path, filename)
            img = Image.open(img_path)
            images.append(img)
    return images


if __name__ == '__main__':
    main()