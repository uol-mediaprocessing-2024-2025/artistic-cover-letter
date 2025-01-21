from concurrent.futures.thread import ThreadPoolExecutor
from functools import lru_cache
import numpy
from PIL.Image import alpha_composite
from PIL.ImageFile import ImageFile
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from image_processing import process_image_blur
from PIL import Image,ImageDraw,ImageFont,ImageChops, ImageFile
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
# Parallelized with the help of AI
def generate_letter_layer(text, font, resolution, images):
    print("Generating letters with text " + str(text) + " and resolution " + str(resolution))
    blank_image, letters, coordinate_x = generate_letter_mask(text, font, resolution)

    # Janky solution to bypass image loading problem
    index = 0
    while len(letters) > len(images):
        images.append(images[index].copy())
        index = (index + 1)%len(letters)

    print("Texturing letters...")
    with ThreadPoolExecutor() as executor:
        textured_letters = list(executor.map(texture_letter, images * len(letters), letters))

    print("Pasting letters...")
    for index, image in enumerate(textured_letters):
        next_letter = Image.new("RGBA", blank_image.size)
        next_letter.paste(image, (coordinate_x[index], 0))
        blank_image = Image.alpha_composite(blank_image, next_letter)

    # Automatic padding
    padding = 0.7
    bbox = blank_image.getbbox()
    new_width = (bbox[3] - bbox[1])+int(resolution*padding)
    new_height = (bbox[2] - bbox[0])+int(resolution*padding)
    x_offset = -bbox[0] + int(padding*resolution/2)
    y_offset = -bbox[1] + int(padding*resolution/2)

    pasted_image = Image.new('RGBA',(new_height, new_width), (0, 0, 0, 0,))
    pasted_image.paste(blank_image, (x_offset, y_offset))
    return pasted_image

# Generates an array of letters as images from a given input resolution
# Parallelized with the help of AI
def generate_letter_mask(text, font_name, resolution):
    # More optimal Text mask code generated by Bing AI
    font_size = resolution #70 is roughly equivalent to 72 pt on 300 DPI A4 paper, tested in Photoshop
    font_files, font_names = get_fonts()
    font_file = font_files[font_names.index(font_name)]
    font = ImageFont.truetype(font_file, font_size)

    # Create a temporary image to get the size of the text
    temp_image = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
    draw = ImageDraw.Draw(temp_image)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Get font metrics for additional padding to avoid text cutoff
    ascent, descent = font.getmetrics()

    # Create the final image with the size adjusted for padding
    image_width = text_width
    image_height = text_height + descent + int(resolution/4)

    blank_image = Image.new('RGBA', (image_width, image_height), (0, 0, 0, 0))

    print("Generating letters...")
    with ThreadPoolExecutor() as executor:
        results = list(executor.map(generate_single_letter, [(char, font, resolution,descent, image_height) for char in text]))

    letters = [res[0] for res in results]
    coordinate_x = [0] + [sum(res[1] for res in results[:i+1]) for i in range(len(results))]
    return blank_image, letters, coordinate_x

def generate_single_letter(args):
    char, font, resolution, descent, image_height = args
    temp_image = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
    draw_temp = ImageDraw.Draw(temp_image)
    text_bbox = draw_temp.textbbox((0, 0), char, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    image = Image.new('RGBA', (text_width, image_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.text((0, int(resolution / 4) - descent), char, font=font, fill="white", align="left")
    return image, int(font.getlength(char))

# Textures letter using an image and the bounding box of the letter
def texture_letter(image, letter):
    # Get dimensions of the letter
    bbox = letter.getbbox()
    # bbox will be none if the letter is empty
    if bbox is None:
        return Image.new('RGBA', letter.size, (0, 0, 0, 0))
    letter_width, letter_height = bbox[2] - bbox[0], bbox[3] - bbox[1]

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

@lru_cache(maxsize=None)
def get_fonts():
    font_files = fontmanager.findSystemFonts()
    font_families = []
    for font in font_files:
        font_name = fontmanager.FontProperties(fname=font).get_name()
        if font_name not in font_families:
            font_families.append(font_name)
    font_data = sorted((fontmanager.FontProperties(fname=font).get_name(), font) for font in font_files)
    sorted_font_families, sorted_font_files = zip(*font_data)
    final_font_families = []
    final_font_files = []
    for index in range(len(sorted_font_families)):
        if sorted_font_families[index] not in final_font_families:
            final_font_families.append(sorted_font_families[index])
            final_font_files.append(sorted_font_files[index])
    return final_font_files, final_font_families