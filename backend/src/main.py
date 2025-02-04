import base64
import concurrent
import json
from concurrent.futures import ThreadPoolExecutor
from typing import List

import numpy
from PIL.Image import alpha_composite
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse

from backend.src.ColorSchemes import cluster_photos
from backend.src.PhotoAnalysis import getSubjects
from backend.src.testing import get_image_colors
from image_processing import process_image_blur, circular_kernel, calcDropshadow, calcBackgroundBleed, calcInnerShadow, \
    calcOutline, resizeImage
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from letter_rendering import generate_letter_layer, get_fonts
import io
import uvicorn
import cv2
import numpy as np
import base64
from old import Font
from old import Letter
from old import LetterText
from old import blend_images
from matplotlib import pyplot as plt

app = FastAPI()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (adjust for production use)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

@app.post("/analyze-photos")
async def analyze_photos(photos: list[UploadFile] = File(...)):
    images_hires = []
    print("Loading photos...")
    for photo in photos:
        data = await photo.read()
        image = Image.open(io.BytesIO(data))
        images_hires.append(image)
    print("Scaling photos...")
    with ThreadPoolExecutor() as executor:
        images = list(executor.map(resizeImage, images_hires))
    print("Analyzing colors...")
    with ThreadPoolExecutor() as executor:
        photo_colors = list(executor.map(get_image_colors, images))
    schemes, groups = cluster_photos(photo_colors)
    content = []
    for scheme in schemes:
        content.append(scheme)
    for group in groups:
        content.append(group)
    return JSONResponse(content=content)

@app.post("/submit-text")
async def submit_text(
        text: str = Form(...),
        font: str = Form(...),
        resolution: int = Form(...),
        dropshadow_radius: int = Form(...),
        dropshadow_intensity: int = Form(...),
        dropshadow_color: str = Form(...),
        bleed_radius: int = Form(...),
        bleed_intensity: int = Form(...),
        shadow_radius: int = Form(...),
        shadow_intensity: int = Form(...),
        shadow_color: str = Form(...),
        outline_width: int = Form(...),
        outline_color: str = Form(...),
        photos: list[UploadFile] = File(...),
):
    images = []
    for photo in photos:
        data = await photo.read()
        image = Image.open(io.BytesIO(data))
        images.append(image)

    letter_layer = generate_letter_layer(text, font, resolution, images)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(calcBackgroundBleed, letter_layer, bleed_radius, bleed_intensity, resolution),
            executor.submit(calcDropshadow, letter_layer, dropshadow_radius, dropshadow_intensity, dropshadow_color, resolution),
            executor.submit(calcInnerShadow, letter_layer, shadow_radius, shadow_intensity, shadow_color, resolution),
            executor.submit(calcOutline, letter_layer, outline_width, outline_color, resolution)
        ]
    layer0, layer1, layer3, layer4 = [f.result() for f in futures]

    full = fullComposite(layer0, layer1, letter_layer, layer3, layer4)

    images_to_encode = [letter_layer, full]
    with ThreadPoolExecutor() as executor:
        encoded_images = list(executor.map(encodeImage, images_to_encode))
    return JSONResponse(content=encoded_images)

@app.post("/apply-effects")
async def apply_effects(
        bleed_radius: int = Form(...),
        bleed_intensity: int = Form(...),
        dropshadow_radius: int = Form(...),
        dropshadow_intensity: int = Form(...),
        dropshadow_color: str = Form(...),
        shadow_radius: int = Form(...),
        shadow_intensity: int = Form(...),
        shadow_color: str = Form(...),
        outline_width: int = Form(...),
        outline_color: str = Form(...),
        resolution: int = Form(...),
        letter_layer_blob: UploadFile = File(...),
):
    letter_layer = Image.open(io.BytesIO(await letter_layer_blob.read()))
    letter_layer.load()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(calcBackgroundBleed, letter_layer, bleed_radius, bleed_intensity, resolution),
            executor.submit(calcDropshadow, letter_layer, dropshadow_radius, dropshadow_intensity, dropshadow_color, resolution),
            executor.submit(calcInnerShadow, letter_layer, shadow_radius, shadow_intensity, shadow_color, resolution),
            executor.submit(calcOutline, letter_layer, outline_width, outline_color, resolution)
        ]
    layer0, layer1, layer3, layer4 = [f.result() for f in futures]

    full = fullComposite(layer0, layer1, letter_layer, layer3, layer4)

    images_to_encode = [letter_layer, full]
    with ThreadPoolExecutor() as executor:
        encoded_images = list(executor.map(encodeImage, images_to_encode))
    return JSONResponse(content=encoded_images)

# Encodes all images to send them back to the frontend
def encodeImage(image):
    image_io = io.BytesIO()
    image.save(image_io, format="PNG", compress_level=1)
    image_io.seek(0)
    return base64.b64encode(image_io.getvalue()).decode('utf-8')

# Composites all images
def fullComposite(layer0, layer1, layer2, layer3, layer4):
    layers01 = alpha_composite(layer0, layer1)
    layers012 = alpha_composite(layers01, layer2)
    layers0123 = alpha_composite(layers012, layer3)
    layers01234 = alpha_composite(layers0123, layer4)
    return layers01234


@app.post("/retrieve-fonts")
async def retrieveFonts():
    font_files, font_names = get_fonts()
    return JSONResponse(content=font_names)

@app.post("/generate-suggestions")
async def generateSuggestions(
        photos: list[UploadFile] = File(...)
):
    images = []
    for photo in photos:
        data = await photo.read()
        image = Image.open(io.BytesIO(data))
        image_scaled = resizeImage(image, 512)
        images.append(image_scaled)
    results = getSubjects(images)
    return JSONResponse(content=results)


# Old
@app.post("/apply-blur")
async def apply_blur(file: UploadFile = File(...)):
    """
    API endpoint to apply a blur effect to an uploaded image.
    :param file: The uploaded image file.
    :return: StreamingResponse containing the blurred image.
    """
    try:
        # Process the image
        blurred_image = await process_image_blur(file)

        # Create a BytesIO object to send the image as a stream
        image_io = io.BytesIO()
        blurred_image.save(image_io, format="PNG")
        image_io.seek(0)

        # Return the blurred image as a stream in the response
        return StreamingResponse(image_io, media_type="image/png")
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"message": "Failed to process image", "error": str(e)},
        )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
