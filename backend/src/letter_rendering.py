import numpy
from PIL.Image import alpha_composite
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from image_processing import process_image_blur
from PIL import Image,ImageDraw,ImageFont,ImageChops
from image_processing import circular_kernel
import matplotlib.pyplot as plt
import os
import time
import matplotlib.image as mpimg
import io
import uvicorn
import cv2
import numpy as np
import base64

# Generates the whole layer of letters
def generate_letter_layer(text, resolution, images):
    blank_image, letters, coordinate_x = generate_letter_mask(text, resolution)
    textured_letters = []
    for index, image in enumerate(letters):
        textured = texture_letter(images[index%len(images)], image)
        textured_letters.append(textured)
    for index, image in enumerate(textured_letters):
        blank_image.paste(image, (coordinate_x[index], 0))

    # Add some padding for effects
    # Change the padding here
    pasted_image = Image.new('RGBA',(blank_image.width+int(resolution*0.9), blank_image.height+int(resolution*0.39)), (0, 0, 0, 0,))
    pasted_image.paste(blank_image, (int(resolution*0.45), int(resolution*0.195)))
    return pasted_image

# Generates an array of letters as images from a given input resolution
def generate_letter_mask(text, resolution):
    print(f"Received text: {text}")

    # More optimal Text mask code generated by Bing AI
    # Define the text and font
    font_path = r'C:\Users\System-Pc\Desktop\impact.ttf'
    font_size = resolution #70 is roughly equivalent to 72 pt on 300 DPI A4 paper, tested in Photoshop
    font = ImageFont.truetype(font_path, font_size)

    # Create a temporary image to get the size of the text
    temp_image = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
    draw = ImageDraw.Draw(temp_image)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Get font metrics for additional padding to avoid text cutoff
    ascent, descent = font.getmetrics()
    padding = 0 # !!! ADD descent and PADDING!!!

    # Create the final image with the size adjusted for padding
    image_width = text_width + padding * 2
    image_height = text_height + descent + int(resolution/4)

    nextLetterX = 0

    letters = []
    coordinate_x = [0]
    blank_image = Image.new('RGBA', (image_width, image_height), (0, 0, 0, 0))

    for char in text:
        #calculate letter size
        temp_image = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        draw_temp = ImageDraw.Draw(temp_image)
        text_bbox = draw_temp.textbbox((0, 0), char, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        image = Image.new('RGBA', (text_width, image_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)

        #draw letter and dilate
        draw.text((0, int(resolution/4) - descent), char, font=font, fill="white", align="left")
        nextLetterX = nextLetterX + text_width
        dilated = cv2.dilate(np.array(image), circular_kernel(int(resolution/200)), iterations=1)

        #add to arrays
        coordinate_x.append(nextLetterX)
        letters.append(Image.fromarray(dilated))
    return blank_image, letters, coordinate_x

# Textures letter using an image and the bounding box of the letter
def texture_letter(image, letter):
    # Get dimensions of the letter
    bbox = letter.getbbox()
    # bbox will be none if the letter is empty
    if bbox is None:
        return Image.new('RGBA', image.size, (0, 0, 0, 0))
    letter_width = bbox[2] - bbox[0]
    letter_height = bbox[3] - bbox[1]

    # Calculate aspect ratio of the image
    aspect_ratio = image.width / image.height

    # Calculate new dimensions for the image to fit within the letters bounding box
    if aspect_ratio > (letter_width / letter_height):
        new_height = letter_height
        new_width = int(letter_height * aspect_ratio)
    else:
        new_height = letter_height
        new_width = int(letter_height * aspect_ratio)

    # Resize the image
    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Create a new blank image with the same dimensions as the full letter image
    centered_image = Image.new('RGBA', (letter.width, letter.height), (0, 0, 0, 0))

    # Calculate the position to paste the resized image to center it
    x_offset = (letter_width - new_width) // 2
    y_offset = bbox[1]

    # Paste the resized image onto the new blank image
    centered_image.paste(resized_image, (x_offset, y_offset))

    # Multiply the image with the mask
    result_image = ImageChops.multiply(centered_image, letter)

    return result_image