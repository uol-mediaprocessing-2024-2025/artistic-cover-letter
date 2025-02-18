from PIL import Image
import os
# Needed for some plots, for some reason
#mpl.use('TkAgg')

def main():

    images = load_images_from_folder("C:/Users/Simon/Downloads/examplePhotos sorted/")

    image = images[0]
    print("Hello world")

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