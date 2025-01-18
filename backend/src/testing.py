import concurrent
from concurrent.futures import ThreadPoolExecutor

import numpy
import psutil
from PIL.Image import alpha_composite
from PIL.ImageQt import rgb
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from scipy.spatial.distance import squareform

from backend.src.ColorSchemes import generate_constant_value, get_frequent_colors, \
    generate_color_schemes, rate_color_pairing, rate_photo_pairing, rate_color_scheme, plot_colors
from backend.src.PhotoAnalysis import getSubjects
from backend.src.image_processing import calcBackgroundBleed, calcDropshadow, calcInnerShadow, circular_kernel, \
    resizeImage

from image_processing import process_image_blur
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageCms
from letter_rendering import generate_letter_layer
import matplotlib.colors as matcolors
import matplotlib.pyplot as plt
import colorspacious as cs
import os
import time
import matplotlib.image as mpimg
import io
import uvicorn
import cv2
import numpy as np
from sklearn.cluster import AgglomerativeClustering, KMeans
import base64
from letter_rendering import generate_letter_mask, texture_letter
from collections import Counter
import moondream as md


def main():

    images = load_images_from_folder("C:/Users/Simon/Downloads/examplePhotos sorted/")

    print("Extracting image colors... ")
    with ThreadPoolExecutor() as executor:
        photo_colors = list(executor.map(get_image_colors, images))

    distance_matrix = np.zeros((len(photo_colors), len(photo_colors)))

    print("Calculating distance matrix... ")
    for i in range(len(photo_colors)):
        for j in range(i, len(photo_colors)):
            if i == j:
                distance_matrix[i, j] = 0
            else:
                distance = rate_photo_pairing(photo_colors[i], photo_colors[j])
                distance_matrix[i, j] = distance
                distance_matrix[j, i] = distance  # Matrix symmetry

    print("Performing clustering... ")
    cluster_count = 3

    kmeans = KMeans(n_clusters=cluster_count)
    cluster_assignments = kmeans.fit_predict(distance_matrix)
    cluster_centers = kmeans.cluster_centers_

    print("Done!")

    print(cluster_assignments)

    closest_points = find_closest_points(cluster_centers, distance_matrix)
    print(closest_points)

    groups = []
    for integer in range(0,cluster_count):
        cluster_group = []
        for index in range(0,len(cluster_assignments)):
            if cluster_assignments[index] == integer:
                cluster_group.append(index)
        groups.append(cluster_group)

    schemes = []
    for index in closest_points:
        schemes.append(photo_colors[index])

    for index in range(0,3):
        plot_colors(schemes[index])
        for j in range(0, len(groups[index])):
            image_index = groups[index][j]
            plt.imshow(images[image_index])
            plt.show()

    # Takes cluster centers and uses the distance matrix to find the center cluster element.
    # Written by Bing AI
def find_closest_points(cluster_centers, distance_matrix):
    closest_points = []
    for center in cluster_centers:
        distances = np.linalg.norm(distance_matrix - center, axis=1)
        closest_point = np.argmin(distances)
        closest_points.append(closest_point)
    return closest_points

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

# Uses an Algorithm by Kamal Joshi to find prominent colors.
# https://hackernoon.com/extract-prominent-colors-from-an-image-using-machine-learning-vy2w33rx
def get_image_colors(image):
    # Resize to 128x128 for performance
    image = image.resize((128,128))
    image = np.array(image)

    # Reshape image to a 2D array of pixels
    srgb_pixels = image.reshape(-1, 3)
    lab_pixels = cs.cspace_convert(srgb_pixels, "sRGB1", "CIELab")

    # Run k-means clustering
    kmeans = KMeans(n_clusters=24)
    kmeans.fit(lab_pixels)

    # Get the cluster centers (dominant colors)
    colors = kmeans.cluster_centers_
    colors = cs.cspace_convert(colors, "CIELab", "sRGB1")

    # Convert color to integer values
    colors_rgb = [list(map(int, color)) for color in colors]

    # Sort by hue
    hue_sorted = sort_colors_by_hsv_component(colors_rgb, 0)

    # Split into six groups
    group1 = hue_sorted[0:4]
    group2 = hue_sorted[4:8]
    group3 = hue_sorted[8:12]
    group4 = hue_sorted[12:16]
    group5 = hue_sorted[16:20]
    group6 = hue_sorted[20:24]

    groups = [group1, group2, group3, group4, group5, group6]
    groupresults = []

    # Perform other group operations
    for group in groups:
        group = sort_colors_by_hsv_component(group, 1)
        group = group[2:4]
        group = sort_colors_by_hsv_component(group, 2)
        groupresults.append(group[1])
    return groupresults

def sort_colors_by_hsv_component(rgb_colors, dimension):
    # normalize rgb and convert to hsv
    normalized = np.array(rgb_colors) / 255.0
    hsv_colors = [matcolors.rgb_to_hsv(color) for color in normalized]

    # Sort the colors by the hue component (first value in HSB)
    sorted_indices = np.argsort([color[dimension] for color in hsv_colors])

    # Return the colors sorted by hue
    return [rgb_colors[i] for i in sorted_indices]


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