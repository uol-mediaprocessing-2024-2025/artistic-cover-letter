import numpy
from PIL.Image import alpha_composite
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from backend.src.image_processing import calcBackgroundBleed, calcDropshadow, calcInnerShadow, circular_kernel
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
from collections import Counter

def main():
    images = load_images_from_folder("C:/Users/Simon/Downloads/examplePhotos2/")
    colors_1 = extract_dominant_colors(images[0])
    colors_2 = extract_dominant_colors(images[1])
    colors_3 = extract_dominant_colors(images[2])
    colors_4 = extract_dominant_colors(images[3])
    colors_5 = extract_dominant_colors(images[4])
    #distance = color_scheme_distance(colors_1, colors_2)
    #print("Total distance: " + str(distance))
    distance = color_scheme_distance(colors_1, colors_3)
    print("Total distance: " + str(distance))
    distance = color_scheme_distance(colors_3, colors_4)
    print("Total distance: " + str(distance))
    #distance = color_scheme_distance(colors_4, colors_5)
    #print("Total distance: " + str(distance))

    plot_colors(colors_3)
    plot_colors(colors_4)

    # todo: implement adjacency list for all images to identify pairs

# Calculates the distance between two color schemes
# Needs improvement
def color_scheme_distance(colors_1, colors_2):
    total_distance = 0
    for index1, color1 in enumerate(colors_1):
        # Iterate through each color for scheme 1
        distance = 255*3
        for index2, color2 in enumerate(colors_2):
            # Iterate through each color from scheme 2 to find the best match (lowest distance)
            r_distance = abs(int(color1[0]) - int(color2[0]))
            g_distance = abs(int(color1[1]) - int(color2[1]))
            b_distance = abs(int(color1[2]) - int(color2[2]))
            new_distance = r_distance + g_distance + b_distance
            if new_distance < distance:
                distance = new_distance
        total_distance = total_distance + distance
        print("Color distance: " + str(distance))
    return total_distance

# Extracts dominant colors, with help from Bing AI
def extract_dominant_colors(image, num_colors=8):
    image = image.resize((100, 100))  # Resize for performance
    image = image.convert('RGB')
    image_array = np.asarray(image)
    image_4bit_array = (image_array // 16) * 16 # Reduce color depth to group more shades together
    dilated = cv2.dilate(image_4bit_array, circular_kernel(1)) # Dilate to reduce number of darker colors, not the best solution
    image = Image.fromarray(dilated)

    pixels = np.array(image).reshape(-1, 3)
    pixel_counts = Counter(map(tuple, pixels))
    dominant_colors = pixel_counts.most_common(num_colors)

    return [color for color, count in dominant_colors]

# Plot the colors as bar chart for testing. Bing AI Method
def plot_colors(colors):
    fig, ax = plt.subplots(1, 1, figsize=(8, 2), subplot_kw=dict(xticks=[], yticks=[], frame_on=False))
    ax.imshow([colors], aspect='auto')
    plt.show()


def main2():
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