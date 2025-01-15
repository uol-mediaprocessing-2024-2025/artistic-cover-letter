import concurrent
from concurrent.futures import ThreadPoolExecutor

import numpy
import psutil
from PIL.Image import alpha_composite
from PIL.ImageQt import rgb
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from backend.src.PhotoAnalysis import getSubjects
from backend.src.image_processing import calcBackgroundBleed, calcDropshadow, calcInnerShadow, circular_kernel, \
    resizeImage
from image_processing import process_image_blur
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageCms
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
import moondream as md

def main():
    images = load_images_from_folder("C:/Users/Simon/Downloads/examplePhotos2/")
    images_small = []
    for image in images:
        image_small = resizeImage(image, 512)
        images_small.append(image_small)
    starttime = time.time()
    answers = getSubjects(images_small)
    print(answers)
    print("Time: " + str(time.time()-starttime))

def main7():
    images = load_images_from_folder("C:/Users/Simon/Downloads/examplePhotos2/")

    # Test sRGB color space
    colors_1_sRGB = extract_dominant_colors(images[0])
    plot_colors(colors_1_sRGB)
    colors_2_sRGB = extract_dominant_colors(images[1])
    plot_colors(colors_2_sRGB)
    distance_sRGB = color_scheme_distance(colors_1_sRGB, colors_2_sRGB)
    print("Distance sRGB: " + str(distance_sRGB))

    # Test Oklab color space
    colors_1_Oklab = extract_dominant_colors_2(images[0])
    plot_colors(colors_1_Oklab)
    colors_2_Oklab = extract_dominant_colors_2(images[1])
    plot_colors(colors_2_Oklab)
    distance_Oklab = color_scheme_distance(colors_1_sRGB, colors_2_sRGB)
    print("Distance Oklab: " + str(distance_Oklab))

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
    image = image.resize((500, 500))  # Resize for performance
    image = image.convert('RGB')
    image_array = np.asarray(image)
    image_4bit_array = (image_array // 16) * 16 # Reduce color depth to group more shades together
    image_4bit_array_img = Image.fromarray(image_4bit_array)
    image_4bit_array_img.show()
    dilated = cv2.dilate(image_4bit_array, circular_kernel(1)) # Dilate to reduce number of darker colors, not the best solution
    image = Image.fromarray(dilated)

    pixels = np.array(image).reshape(-1, 3)
    pixel_counts = Counter(map(tuple, pixels))
    dominant_colors = pixel_counts.most_common(num_colors)

    return [color for color, count in dominant_colors]

def extract_dominant_colors_2(image, num_colors=8):
    image = image.resize((500, 500))  # Resize for performance

    image_lab = rgb_to_lab(image)
    image_lab_array = np.asarray(image_lab)
    image_lab_array = np.array(image_lab, dtype=np.float32).copy()

    image_lab_array[..., 0] = (image_lab_array[..., 0] / 255.0) * 100.0  # Normalize L* to [0, 100]
    image_lab_array[..., 1:] = image_lab_array[..., 1:] - 128.0  # Center a* and b* around 0

    # Reduce color depth
    image_4bit_array = (image_lab_array // 16) * 16

    # Denormalize LAB values
    image_4bit_array[..., 0] = (image_4bit_array[..., 0] / 100.0) * 255.0  # Scale L* back to [0, 255]
    image_4bit_array[..., 1:] = image_4bit_array[..., 1:] + 128.0  # Shift a* and b* back to [0, 255]

    # Convert back to image format
    image_lab_reduced = Image.fromarray(np.uint8(image_4bit_array), 'LAB')

    # Convert reduced LAB back to RGB
    image_rgb_reduced = lab_to_rgb(image_lab_reduced)

    image_rgb_reduced.show()

    image_4bit_rgb_array = np.array(image_rgb_reduced)
    dilated = cv2.dilate(image_4bit_rgb_array, circular_kernel(1)) # Dilate to reduce number of darker colors, not the best solution
    image = Image.fromarray(dilated)

    pixels = np.array(image).reshape(-1, 3)
    pixel_counts = Counter(map(tuple, pixels))
    dominant_colors = pixel_counts.most_common(num_colors)

    return [color for color, count in dominant_colors]

def rgb_to_lab(image):
    srgb_p = ImageCms.createProfile("sRGB")
    lab_p = ImageCms.createProfile("LAB")

    rgb2lab = ImageCms.buildTransformFromOpenProfiles(srgb_p, lab_p, "RGB", "LAB")
    Lab = ImageCms.applyTransform(image, rgb2lab)
    return Lab

def lab_to_rgb(image):
    srgb_p = ImageCms.createProfile("sRGB")
    lab_p = ImageCms.createProfile("LAB")

    lab2rgb = ImageCms.buildTransformFromOpenProfiles(lab_p, srgb_p, "LAB", "RGB")
    Rgb = ImageCms.applyTransform(image, lab2rgb)
    return Rgb

# RGB to Oklab function written by Bing AI
def rgb_to_oklab(rgb):
    r, g, b = rgb / 255.0
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b

    l = np.cbrt(l)
    m = np.cbrt(m)
    s = np.cbrt(s)

    l_ = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    a_ = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    b_ = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s

    return np.array([l_, a_, b_])

# Oklab to RGB function written by Bing AI

def oklab_to_rgb(oklab):
    l_, a_, b_ = oklab

    l = l_ + 0.3963377774 * a_ + 0.2158037573 * b_
    m = l_ - 0.1055613458 * a_ - 0.0638541728 * b_
    s = l_ - 0.0894841775 * a_ - 1.2914855480 * b_

    l = l**3
    m = m**3
    s = s**3

    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    b = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s

    return np.clip(np.array([r, g, b]) * 255, 0, 255).astype(np.uint8)


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