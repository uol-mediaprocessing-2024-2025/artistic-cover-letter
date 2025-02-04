from PIL import Image, ImageFilter, ImageOps
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
def calcDropshadow(layer_2, radius, intensity, color, resolution):
    if intensity < 1:
        return Image.new('RGBA', layer_2.size, (0, 0, 0, 0))
    print("Applying dropshadow with radius " + str(radius) + " and intensity " + str(intensity))
    correctedradius = radius * resolution / 300
    correctedradius = round(correctedradius)

    # Handle dropshadow with Alpha channel and set all other channels to black
    r, g, b, a = layer_2.split()
    dilated = cv2.dilate(np.array(a), circular_kernel(int(correctedradius / 4)), iterations=1)
    blurred = cv2.GaussianBlur(dilated, (correctedradius * 2 + 1, correctedradius * 2 + 1), 0)
    dimmed = np.clip(blurred * (intensity/100), 0, 255).astype(np.uint8)
    red = np.array(r)
    red[:] = int(color[1:3], 16)
    green = np.array(g)
    green[:] = int(color[3:5], 16)
    blue = np.array(b)
    blue[:] = int(color[5:7], 16)
    dropshadow = Image.merge("RGBA", (Image.fromarray(red), Image.fromarray(green), Image.fromarray(blue), Image.fromarray(dimmed)))
    return dropshadow

# Calculates the background bleed layer
def calcBackgroundBleed(layer2, radius, intensity, resolution):
    if intensity < 1:
        return Image.new('RGBA', layer2.size, (0, 0, 0, 0))
    print("Applying background bleed with radius " + str(radius) + " and intensity " + str(intensity))
    downscalefactor = 2
    if resolution >= 600:
        downscalefactor = 4
        if resolution >= 1200:
            downscalefactor = 8
            if resolution >= 2400:
                downscalefactor = 16
    downscaled = layer2.resize((int(layer2.width/downscalefactor), int(layer2.height/downscalefactor)), Image.Resampling.NEAREST)
    correctedradius = int((radius*(resolution/200))/downscalefactor)
    dilated = Image.fromarray(cv2.dilate(np.array(downscaled), circular_kernel(correctedradius)))
    r1, g1, b1, a1 = dilated.split()
    r2, g2, b2, a2 = downscaled.split()
    background = Image.merge("RGBA", (r1, g1, b1, a2))
    blurred_background = background.filter(ImageFilter.GaussianBlur(radius=correctedradius))
    r3, g3, b3, a3 = blurred_background.split()
    multiplied_alpha = np.array(a3) * (intensity/100 + radius/100)
    clipped_alpha = np.clip(multiplied_alpha, 0, 255).astype(np.uint8)
    final = Image.merge("RGBA", (r3, g3, b3, Image.fromarray(clipped_alpha, "L")))
    final_upscaled = final.resize(layer2.size, Image.Resampling.BILINEAR)
    return final_upscaled

def calcInnerShadow(layer2, radius, intensity, color, resolution):
    if intensity < 1:
        return Image.new('RGBA', layer2.size, (0, 0, 0, 0))
    print("Applying inner shadow with radius " + str(radius) + " and intensity " + str(intensity))
    correctedradius = int(radius*(resolution/600))
    r, g, b, a = layer2.split()
    r2 = Image.fromarray(np.full((r.height,r.width), int(color[1:3], 16), dtype=np.uint8))
    g2 = Image.fromarray(np.full((g.height, g.width), int(color[3:5], 16), dtype=np.uint8))
    b2 = Image.fromarray(np.full((b.height, b.width), int(color[5:7], 16), dtype=np.uint8))
    inverted_alpha = ImageOps.invert(a)
    blurred_alpha = inverted_alpha.filter(ImageFilter.GaussianBlur(radius=correctedradius))

    multiplied_alpha = ((np.array(a)/255)*intensity/75) * np.array(blurred_alpha)
    clipped_alpha = np.clip(multiplied_alpha, 0, 255).astype(np.uint8)
    clipped_alpha_image = Image.fromarray(clipped_alpha, 'L')

    result = Image.merge("RGBA", (r2, g2, b2, clipped_alpha_image))
    return result

def calcOutline(layer2, width, color, resolution):
    if width < 1:
        return Image.new('RGBA', layer2.size, (0, 0, 0, 0))
    print("Applying outline with width " + str(width))
    correctedwidth = int(width*(resolution/2000))
    r, g, b, a = layer2.split()
    r2 = Image.fromarray(np.full((r.height,r.width), int(color[1:3], 16), dtype=np.uint8))
    g2 = Image.fromarray(np.full((g.height, g.width), int(color[3:5], 16), dtype=np.uint8))
    b2 = Image.fromarray(np.full((b.height, b.width), int(color[5:7], 16), dtype=np.uint8))
    dilated = cv2.dilate(np.array(a), circular_kernel(correctedwidth), iterations=1)
    inverted_alpha = ImageOps.invert(a)
    multiplied = np.array(dilated) * (np.array(inverted_alpha)/255)
    clipped_alpha = np.clip(multiplied, 0, 255).astype(np.uint8)
    clipped_alpha_image = Image.fromarray(clipped_alpha, 'L')
    result = Image.merge("RGBA", (r2, g2, b2, clipped_alpha_image))
    return result

# Resize image to dimension parameter pixles on the longest dimension
def resizeImageLongest(image, dimension=128):
    width, height = image.size
    if width > height:
        new_width = dimension
        new_height = int((height/width)*dimension)
    else:
        new_height = dimension
        new_width = int((width/height)*dimension)
    return image.resize((new_width, new_height))

# Resize image to dimension parameter pixles on the shortest dimension
def resizeImageShortest(image, dimension=256):
    width, height = image.size
    if width < height:
        new_width = dimension
        new_height = int((height / width) * dimension)
    else:
        new_height = dimension
        new_width = int((width / height) * dimension)
    return image.resize((new_width, new_height))



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
