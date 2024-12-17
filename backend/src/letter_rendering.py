import numpy
from PIL.Image import alpha_composite
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from image_processing import process_image_blur
from PIL import Image,ImageDraw,ImageFont,ImageChops
from image_processing import circular_kernel
import matplotlib.font_manager as fontmanager
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
def generate_letter_layer(text, font, resolution, images):
    print("Generating letters with text " + str(text) + " and resolution " + str(resolution))
    blank_image, letters, coordinate_x = generate_letter_mask(text, font, resolution)
    textured_letters = []
    for index, image in enumerate(letters):
        textured = texture_letter(images[index%len(images)], image)
        textured_letters.append(textured)
    for index, image in enumerate(textured_letters):
        next_letter = Image.new("RGBA", blank_image.size)
        next_letter.paste(image, (coordinate_x[index], 0))
        blank_image = Image.alpha_composite(blank_image, next_letter)

    # Automatic padding
    padding = 0.8
    bbox = blank_image.getbbox()
    new_width = (bbox[3] - bbox[1])+int(resolution*padding)
    new_height = (bbox[2] - bbox[0])+int(resolution*padding)
    x_offset = -bbox[0] + int(padding*resolution/2)
    y_offset = -bbox[1] + int(padding*resolution/2)

    pasted_image = Image.new('RGBA',(new_height, new_width), (0, 0, 0, 0,))
    pasted_image.paste(blank_image, (x_offset, y_offset))
    return pasted_image

# Generates an array of letters as images from a given input resolution
def generate_letter_mask(text, font_name, resolution):
    # More optimal Text mask code generated by Bing AI
    # Define the text and font
    font_files, font_names = get_fonts()
    font_path = r'C:\Users\System-Pc\Desktop\impact.ttf'
    for font in font_files:
        font_properties = fontmanager.FontProperties(fname=font)
        if font_properties.get_name() == font_name and font_properties.get_style() == 'normal':
            font_path = font
            break

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
    print("Ascent: " + str(ascent))
    print("Descent: " + str(descent))

    # Create the final image with the size adjusted for padding
    image_width = text_width
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
        nextLetterX = nextLetterX + int(font.getlength(char, "")) #needs actual letter width

        #add to arrays
        coordinate_x.append(nextLetterX)
        letters.append(image)
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
    image_aspect_ratio = image.width / image.height
    letter_aspect_ratio = letter_width / letter_height

    # Calculate new dimensions for the image to fit within the letters bounding box
    if image_aspect_ratio > letter_aspect_ratio:
        new_height = letter_height
        new_width = int(letter_height * image_aspect_ratio)
    else:
        new_width = letter_width
        new_height = int(letter_width / image_aspect_ratio)

    # Resize the image
    resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    # Create a new blank image with the same dimensions as the full letter image
    centered_image = Image.new('RGBA', (letter.width, letter.height), (0, 0, 0, 0))

    # Calculate the position to paste the resized image to center it
    x_offset = bbox[0] + int((letter_width - new_width) / 2)
    y_offset = bbox[1] + int((letter_height - new_height) / 2)

    # Paste the resized image onto the new blank image
    centered_image.paste(resized_image, (x_offset, y_offset))

    # Multiply the image with the mask
    result_image = ImageChops.multiply(centered_image, letter)

    return result_image

def get_fonts():
    font_files = fontmanager.findSystemFonts()
    font_families = []
    for font in font_files:
        font_name = fontmanager.FontProperties(fname=font).get_name()
        print(font_name)
        if font_name not in font_families:
            font_families.append(font_name)
    return sorted(font_files), sorted(font_families)