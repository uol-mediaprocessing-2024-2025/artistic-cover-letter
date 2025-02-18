# Includes dead code that can be used in the future
from collections import Counter

import cv2
import numpy as np
from PIL import Image
from PIL.Image import alpha_composite
import colorspacious as cs
import matplotlib.colors as matcolors
from matplotlib import pyplot as plt

from backend.src.image_processing import calcBackgroundBleed, calcDropshadow, calcInnerShadow, circular_kernel
from backend.src.letter_rendering import generate_letter_layer
from backend.src.testing import load_images_from_folder

# Generates an example video
def generate_video():
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

# Returns array with linear interpolation between start value and end value
def linear_interpolation(startvalue, endvalue):
    diff = endvalue - startvalue
    values = []
    for index in range(0,120):
        newvalue = startvalue + index * (diff/120)
        values.append(newvalue)
    return values

#  --- Old color functions ---

# Oklab to RGB function written by Bing AI
# Unused in favor of CIELab
# Probably wrong anyway
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

# RGB to Oklab function written by Bing AI
# Unused in favor of CIELab
# Probably wrong anyway
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

# Old method to extract dominant colors, with help from Bing AI
# Doesn't work very well
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

# Takes in an RGB color and varies all HSV dimensions except the one that
# is given in constant_dimension
def generate_hsv_variations(color, constant_dimension):
    color = np.array(color)
    normalized = color/255.0
    hsv = matcolors.rgb_to_hsv(normalized)
    constant = hsv[constant_dimension]
    hsv = np.delete(hsv, constant_dimension)
    variable1 = hsv[0]
    variable2 = hsv[1]
    depth = 8
    colors = []
    for variable1_offset in range(1,depth):
        variable1_offset = (variable1_offset / depth)/5
        # Ensure that variable 1 is within 0 and 1
        if ((variable1 + (-2) * variable1_offset) > 0) & (variable1 + 2 * variable1_offset < 1):
            for variable2_offset in range(1,depth):
                variable2_offset = (variable2_offset / depth)/5
                # Ensure that variable 2 is within 0 and 1
                if ((variable2 + (-2) * variable2_offset) > 0) & (variable2 + 2 * variable2_offset < 1):
                    color_scheme = []
                    for pallet_offset in range(5):
                        hsv_variable1 = variable1 + ((pallet_offset - 2) * variable1_offset)
                        hsv_variable2 = variable2 + ((pallet_offset - 2) * variable2_offset)
                        match constant_dimension:
                            case 0: hsv = np.array([constant, hsv_variable1, hsv_variable2])
                            case 1: hsv = np.array([hsv_variable1, constant, hsv_variable2])
                            case 2: hsv = np.array([hsv_variable1, hsv_variable2, constant])
                        rgb = matcolors.hsv_to_rgb(hsv)
                        rgb = (rgb*255).astype(np.uint8)
                        color_scheme.append(rgb)
                    colors.append(color_scheme)
    return colors

# Generates colors with constant value
def generate_constant_value(value):
    colors = []
    for hue in range(0, 7):
        for saturation in range(0, 7):
            hue = hue*(365/8)
            rad = np.deg2rad(hue)
            a = 100 * np.cos(rad)
            b = 100 * np.sin(rad)
            value = 1
            a = 0
            b = 0
            cielab = np.array([value, a, b])
            rgb = cs.cspace_convert(cielab, "CIELab", "sRGB1")
            print(rgb)
            colors.append(rgb)
    return colors

# Compare histograms between images
def compare_histograms(image1, image2):
    # AI generated histogram code to quickly test different methods


    # Calculate histogram for each color channel (B, G, R)
    hist1_b = cv2.calcHist([image1], [0], None, [256], [0, 256])
    hist1_g = cv2.calcHist([image1], [1], None, [256], [0, 256])
    hist1_r = cv2.calcHist([image1], [2], None, [256], [0, 256])

    hist2_b = cv2.calcHist([image2], [0], None, [256], [0, 256])
    hist2_g = cv2.calcHist([image2], [1], None, [256], [0, 256])
    hist2_r = cv2.calcHist([image2], [2], None, [256], [0, 256])

    # Normalize histograms
    hist1_b = cv2.normalize(hist1_b, hist1_b).flatten()
    hist1_g = cv2.normalize(hist1_g, hist1_g).flatten()
    hist1_r = cv2.normalize(hist1_r, hist1_r).flatten()

    hist2_b = cv2.normalize(hist2_b, hist2_b).flatten()
    hist2_g = cv2.normalize(hist2_g, hist2_g).flatten()
    hist2_r = cv2.normalize(hist2_r, hist2_r).flatten()

    # Method 1: Correlation
    correlation_b = cv2.compareHist(hist1_b, hist2_b, cv2.HISTCMP_CORREL)
    correlation_g = cv2.compareHist(hist1_g, hist2_g, cv2.HISTCMP_CORREL)
    correlation_r = cv2.compareHist(hist1_r, hist2_r, cv2.HISTCMP_CORREL)

    # Method 2: Chi-Square
    chi_square_b = cv2.compareHist(hist1_b, hist2_b, cv2.HISTCMP_CHISQR)
    chi_square_g = cv2.compareHist(hist1_g, hist2_g, cv2.HISTCMP_CHISQR)
    chi_square_r = cv2.compareHist(hist1_r, hist2_r, cv2.HISTCMP_CHISQR)

    # Method 3: Intersection
    intersection_b = cv2.compareHist(hist1_b, hist2_b, cv2.HISTCMP_INTERSECT)
    intersection_g = cv2.compareHist(hist1_g, hist2_g, cv2.HISTCMP_INTERSECT)
    intersection_r = cv2.compareHist(hist1_r, hist2_r, cv2.HISTCMP_INTERSECT)

    # Method 4: Bhattacharyya Distance
    bhattacharyya_b = cv2.compareHist(hist1_b, hist2_b, cv2.HISTCMP_BHATTACHARYYA)
    bhattacharyya_g = cv2.compareHist(hist1_g, hist2_g, cv2.HISTCMP_BHATTACHARYYA)
    bhattacharyya_r = cv2.compareHist(hist1_r, hist2_r, cv2.HISTCMP_BHATTACHARYYA)

    correlation_average = (abs(correlation_b) + abs(correlation_g) + abs(correlation_r))/3
    chi_square_average = (abs(chi_square_b) + abs(chi_square_g) + abs(chi_square_r))/3
    intersection_average = (abs(intersection_b) + abs(intersection_g) + abs(intersection_r))/3
    bhattacharyya_average =  (abs(bhattacharyya_b) + abs(bhattacharyya_g) + abs(bhattacharyya_r))/3

    print(f'Correlation avg: {correlation_average}')
    print(f'Chi-Square avg: {chi_square_average}')
    print(f'Intersection avg: {intersection_average}')
    print(f'Bhattacharyya avg: {bhattacharyya_average}')

# Get average hue for an image
def average_hue(image):

    # Convert the image to HSV
    hsv_image = image.convert('HSV')

    # Extract the H channel (Hue)
    hue_data = np.array(hsv_image)[:, 0, 0]  # H channel is the first channel in HSV

    # Calculate the average hue
    average_hue = np.mean(hue_data)

    return average_hue

# Draw hue histogram (version 1)
def draw_hue_histogram(image):

    # Convert the image to HSV color space
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Extract the hue channel
    hue_channel = hsv_image[:, :, 0]

    plt.imshow(hue_channel)

    # Calculate the histogram for the hue channel
    hist = cv2.calcHist([hue_channel], [0], None, [180], [0, 180])

    # Plot the histogram using matplotlib
    plt.figure(figsize=(10, 6))
    plt.title('Hue Histogram')
    plt.xlabel('Hue Value')
    plt.ylabel('Frequency')
    plt.plot(hist, color='orange')
    plt.xlim([0, 180])
    plt.show()

# Draw hue histogram (version 2)
def draw_hue_histogram_2(image):
    # Convert the image to HSV color space
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Extract the hue, saturation, and value channels
    hue_channel = hsv_image[:, :, 0]
    saturation_channel = hsv_image[:, :, 1]
    value_channel = hsv_image[:, :, 2]

    # Create a mask for pixels with brightness (value) greater than x
    brightness_mask = value_channel > 140

    # Apply the mask to the hue channel
    hue_channel_filtered = hue_channel[brightness_mask]

    # Calculate the histogram for the filtered hue channel
    hist = cv2.calcHist([hue_channel_filtered], [0], None, [180], [0, 180])

    # Plot the histogram using matplotlib
    plt.figure(figsize=(10, 6))
    plt.title('Hue Histogram (Brightness > x')
    plt.xlabel('Hue Value')
    plt.ylabel('Frequency')
    plt.plot(hist, color='orange')
    plt.xlim([0, 180])
    plt.show()