import numpy
from PIL.Image import alpha_composite
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from backend.src.image_processing import calcBackgroundBleed, calcDropshadow, calcInnerShadow
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

    innerShadowIntensity = linear_interpolation(300, 70)
    innershadowRadius = linear_interpolation(120, 15)

    backgroundBleedIntensity = linear_interpolation(0, 68)
    backgroundBleedRadius = linear_interpolation(0, 20)

    dropshadowIntensity = linear_interpolation(0, 33)
    dropshadowRadius = linear_interpolation(0, 7)

    resolution = 1200

    frames = []

    #previous frames
    layer2 = generate_letter_layer("Video", resolution, images)
    layer0 = calcBackgroundBleed(layer2, backgroundBleedRadius[0], backgroundBleedIntensity[0], resolution)
    layer1 = calcDropshadow(layer2, dropshadowRadius[0], dropshadowIntensity[0], "#000000", resolution)
    layer3 = calcInnerShadow(layer2, innershadowRadius[0], innerShadowIntensity[0], "#FFFFFF", resolution)
    full_frame = alpha_composite(layer0, layer1)
    full_frame2 = alpha_composite(full_frame, layer2)
    full_frame3 = alpha_composite(full_frame2, layer3)
    full_frame4 = alpha_composite(Image.new('RGBA', layer2.size, (255, 255, 255, 255)), full_frame3)
    for index in range(0, 120):
        frames.append(full_frame4)

    # animation
    for index in range(0, 120):
        layer2 = generate_letter_layer("Video", resolution, images)
        layer0 = calcBackgroundBleed(layer2, backgroundBleedRadius[index], backgroundBleedIntensity[index], resolution)
        layer1 = calcDropshadow(layer2, dropshadowRadius[index], dropshadowIntensity[index], "#000000", resolution)
        layer3 = calcInnerShadow(layer2, innershadowRadius[index], innerShadowIntensity[index], "#FFFFFF", resolution)
        full_frame = alpha_composite(layer0, layer1)
        full_frame2 = alpha_composite(full_frame, layer2)
        full_frame3 = alpha_composite(full_frame2, layer3)
        full_frame4 = alpha_composite(Image.new('RGBA', layer2.size, (255, 255, 255, 255)), full_frame3)
        frames.append(full_frame4)

    #previous frames
    layer2 = generate_letter_layer("Video", resolution, images)
    layer0 = calcBackgroundBleed(layer2, backgroundBleedRadius[119], backgroundBleedIntensity[119], resolution)
    layer1 = calcDropshadow(layer2, dropshadowRadius[119], dropshadowIntensity[119], "#000000", resolution)
    layer3 = calcInnerShadow(layer2, innershadowRadius[119], innerShadowIntensity[119], "#FFFFFF", resolution)
    full_frame = alpha_composite(layer0, layer1)
    full_frame2 = alpha_composite(full_frame, layer2)
    full_frame3 = alpha_composite(full_frame2, layer3)
    full_frame4 = alpha_composite(Image.new('RGBA', layer2.size, (255, 255, 255, 255)), full_frame3)
    for index in range(0, 120):
        frames.append(full_frame4)

    video = cv2.VideoWriter('output_video.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 60, (frames[0].width, frames[0].height))
    for frame in frames:
        video.write(cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR))

    video.release()

def linear_interpolation(startvalue, endvalue):
    diff = endvalue - startvalue
    values = []
    for index in range(0,120):
        newvalue = startvalue + index * (diff/120)
        values.append(newvalue)
    return values



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