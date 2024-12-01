import numpy
from PIL.Image import alpha_composite
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from backend.src.image_processing import calcBackgroundBleed, calcDropshadow
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
    # Proof of concept animation
    images = load_images_from_folder("C:/Users/Simon/Downloads/examplePhotos")

    frames = []
    for index in range(0, 180):
        layer2 = generate_letter_layer("Video", 300, images)
        layer0 = calcBackgroundBleed(layer2, index, 80, 300)
        layer1 = calcDropshadow(layer2, 10, index-50, "#000000", 300)
        full_frame = alpha_composite(layer0, layer1)
        full_frame2 = alpha_composite(full_frame, layer2)
        frames.append(full_frame2)

    video = cv2.VideoWriter('output_video.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 30, (frames[0].width, frames[0].height))
    for frame in frames:
        video.write(cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR))

    video.release()



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