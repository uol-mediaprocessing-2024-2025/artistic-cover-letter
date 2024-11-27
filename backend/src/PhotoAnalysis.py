import numpy as np
import os
from PIL import Image
import cv2

def main():
    folder_path = "C:/Users/Simon/Downloads/examplePhotos sorted/"
    for filename in os.listdir(folder_path):
        # Construct full file path
        file_path = os.path.join(folder_path, filename)
        try:
            # Open the image file
            with Image.open(file_path) as img:
                print(f'Opened image: {filename}')
                os.rename(file_path, os.path.join(folder_path, str(average_hue(img))) + ".jpg")
        except OSError:
            print(f'File {filename} is not a valid image')


def average_hue(image):

    # Convert the image to HSV
    hsv_image = image.convert('HSV')

    # Extract the H channel (Hue)
    hue_data = np.array(hsv_image)[:, :, 0]  # H channel is the first channel in HSV

    # Calculate the average hue
    average_hue = np.mean(hue_data)

    return average_hue



if __name__ == '__main__':
    main()