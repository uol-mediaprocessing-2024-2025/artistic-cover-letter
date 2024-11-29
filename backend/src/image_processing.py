from PIL import Image, ImageFilter
import numpy as np
import cv2
import io

# Creates a circular kernel for dilation
def circular_kernel(radius):
    # Create a square grid of size (2*radius+1) x (2*radius+1)
    size = 2 * radius + 1
    kernel = np.zeros((size, size), dtype=np.uint8)

    # Calculate the center of the kernel
    center = radius

    # Fill the kernel with a circular pattern
    for i in range(size):
        for j in range(size):
            if np.sqrt((i - center) ** 2 + (j - center) ** 2) <= radius:
                kernel[int(i), int(j)] = 1

    return kernel

# Calculates the dropshadow layer
def calcDropshadow(layer_2, radius, intensity, resolution):
    if intensity > 1:
        intensity = intensity / 100
        if radius > 100:
            print(f"dropshadow limited to 100 units radius")
            radius = 100
        if radius < 1:
            radius = 1
        if resolution > 2400:
            resolution = 2400
        if resolution < 1:
            resolution = 1
        radius = radius * resolution / 300
        radius = round(radius)
        print(f"Received dropshadow: {radius}")

        # Handle dropshadow with Alpha channel and set all other channels to black
        r, g, b, a = layer_2.split()
        dilated = cv2.dilate(np.array(a), circular_kernel(radius), iterations=1)
        blurred = cv2.GaussianBlur(dilated, (radius * 4 + 1, radius * 4 + 1), 0)
        dimmed = np.clip(blurred * intensity, 0, 255).astype(np.uint8)
        red = np.array(r)
        red[:] = 0
        green = np.array(g)
        green[:] = 0
        blue = np.array(b)
        blue[:] = 0
        dropshadow = Image.merge("RGBA", (Image.fromarray(red), Image.fromarray(green), Image.fromarray(blue), Image.fromarray(dimmed)))
        return dropshadow
    else:
        return Image.new('RGBA', layer_2.size, (0, 0, 0, 0))

# Calculates the background bleed layer
def calcBackgroundBleed(layer2, radius, intensity, resolution):
    correctedradius = int(radius*(resolution/200))
    dilated = Image.fromarray(cv2.dilate(np.array(layer2), circular_kernel(correctedradius)))
    r1, g1, b1, a1 = dilated.split()
    r2, g2, b2, a2 = layer2.split()
    background = Image.merge("RGBA", (r1, g1, b1, a2))
    blurred_background = background.filter(ImageFilter.GaussianBlur(radius=correctedradius))


    return blurred_background

async def process_image_blur(file):
    """
    Applies a blur effect to the uploaded image.
    :param file: The uploaded image file.
    :return: The processed (blurred) PIL Image object.
    """
    # Read the image file data
    image_data = await file.read()

    # Open the image using PIL
    image = Image.open(io.BytesIO(image_data))

    # Apply the blur effect
    blurred_image = image.filter(ImageFilter.BoxBlur(50))

    return blurred_image
