import numpy
from PIL.Image import alpha_composite
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from image_processing import process_image_blur
from PIL import Image,ImageDraw,ImageFont,ImageChops
from letter_rendering import generate_letter_layer
import matplotlib.pyplot as plt
import os
import time
import matplotlib.image as mpimg
import io
import uvicorn
import cv2
import numpy as np
import base64
from letter_rendering import generate_letter_mask, texture_letter

def main():

    images = load_images_from_folder("C:/Users/Simon/Downloads/examplePhotos")

    img = generate_letter_layer("Test", 200, images)

    imgplot = plt.imshow(img)
    plt.show()

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