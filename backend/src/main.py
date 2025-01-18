import base64
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
    images = []
    for photo in photos:
        data = await photo.read()
        image = Image.open(io.BytesIO(data))
        image = image.resize((128,128)) # Resize to 128x128 for performance
        images.append(image)
    with ThreadPoolExecutor() as executor:
        photo_colors = list(executor.map(get_image_colors, images))
    schemes, groups = cluster_photos(photo_colors)
    content = []
    for scheme in schemes:
        content.append(scheme)
    print(schemes)
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

    layer2 = generate_letter_layer(text, font, resolution, images)
    layer0 = calcBackgroundBleed(layer2, bleed_radius, bleed_intensity, resolution)
    layer1 = calcDropshadow(layer2, dropshadow_radius, dropshadow_intensity, dropshadow_color, resolution)
    layer3 = calcInnerShadow(layer2, shadow_radius, shadow_intensity, shadow_color, resolution)
    layer4 = calcOutline(layer2, outline_width, outline_color, resolution)

    full = fullComposite(layer0, layer1, layer2, layer3, layer4)

    images_to_encode = [full, layer0, layer1, layer2, layer3, layer4]
    with ThreadPoolExecutor() as executor:
        encoded_images = list(executor.map(encodeImage, images_to_encode))
    return JSONResponse(content=encoded_images)

@app.post("/background-bleed")
async def background_bleed(
        radius: int = Form(...),
        intensity: int = Form(...),
        resolution: int = Form(...),
        layer1_blob: UploadFile = File(...),
        layer2_blob: UploadFile = File(...),
        layer3_blob: UploadFile = File(...),
        layer4_blob: UploadFile = File(...),
):
    layer1 = Image.open(io.BytesIO(await layer1_blob.read()))
    layer2 = Image.open(io.BytesIO(await layer2_blob.read()))
    layer3 = Image.open(io.BytesIO(await layer3_blob.read()))
    layer4 = Image.open(io.BytesIO(await layer4_blob.read()))

    layer0 = calcBackgroundBleed(layer2, radius, intensity, resolution)
    full_image = fullComposite(layer0, layer1, layer2, layer3, layer4)
    images_to_encode = [full_image, layer0, layer1, layer2, layer3, layer4]
    with ThreadPoolExecutor() as executor:
        encoded_images = list(executor.map(encodeImage, images_to_encode))
    return JSONResponse(content=encoded_images)

# Encodes all images to send them back to the frontend
def encodeImage(image):
    image_io = io.BytesIO()
    image.save(image_io, format="PNG")
    image_io.seek(0)
    return base64.b64encode(image_io.getvalue()).decode('utf-8')

# Composites all images
def fullComposite(layer0, layer1, layer2, layer3, layer4):
    layers01 = alpha_composite(layer0, layer1)
    layers012 = alpha_composite(layers01, layer2)
    layers0123 = alpha_composite(layers012, layer3)
    layers01234 = alpha_composite(layers0123, layer4)
    return layers01234

# Response to dropshadow request. Changes dropshadow.
@app.post("/dropshadow")
async def dropshadow(
        radius: int = Form(...), intensity: int = Form(...), resolution: int = Form(...), color: str = Form(...),
        layer0_blob: UploadFile = File(...),
        layer2_blob: UploadFile = File(...),
        layer3_blob: UploadFile = File(...),
        layer4_blob: UploadFile = File(...),
):
    layer0 = Image.open(io.BytesIO(await layer0_blob.read()))
    layer2 = Image.open(io.BytesIO(await layer2_blob.read()))
    layer3 = Image.open(io.BytesIO(await layer3_blob.read()))
    layer4 = Image.open(io.BytesIO(await layer4_blob.read()))

    layer1 = calcDropshadow(layer2, radius, intensity, color, resolution)
    full_image = fullComposite(layer0, layer1, layer2, layer3, layer4)
    images_to_encode = [full_image, layer0, layer1, layer2, layer3, layer4]
    with ThreadPoolExecutor() as executor:
        encoded_images = list(executor.map(encodeImage, images_to_encode))
    return JSONResponse(content=encoded_images)

@app.post("/inner-shadow")
async def innerShadow(
        radius: int = Form(...),
        intensity: int = Form(...),
        resolution: int = Form(...),
        color: str = Form(...),
        layer0_blob: UploadFile = File(...),
        layer1_blob: UploadFile = File(...),
        layer2_blob: UploadFile = File(...),
        layer4_blob: UploadFile = File(...),
):
    layer0 = Image.open(io.BytesIO(await layer0_blob.read()))
    layer1 = Image.open(io.BytesIO(await layer1_blob.read()))
    layer2 = Image.open(io.BytesIO(await layer2_blob.read()))
    layer4 = Image.open(io.BytesIO(await layer4_blob.read()))

    layer3 = calcInnerShadow(layer2, radius, intensity, color, resolution)
    full_image = fullComposite(layer0, layer1, layer2, layer3, layer4)
    images_to_encode = [full_image, layer0, layer1, layer2, layer3, layer4]
    with ThreadPoolExecutor() as executor:
        encoded_images = list(executor.map(encodeImage, images_to_encode))
    return JSONResponse(content=encoded_images)

@app.post("/outline")
async def outline(
        width: int = Form(...),
        resolution: int = Form(...),
        color: str = Form(...),
        layer0_blob: UploadFile = File(...),
        layer1_blob: UploadFile = File(...),
        layer2_blob: UploadFile = File(...),
        layer3_blob: UploadFile = File(...),
):
    layer0 = Image.open(io.BytesIO(await layer0_blob.read()))
    layer1 = Image.open(io.BytesIO(await layer1_blob.read()))
    layer2 = Image.open(io.BytesIO(await layer2_blob.read()))
    layer3 = Image.open(io.BytesIO(await layer3_blob.read()))

    layer4 = calcOutline(layer2, width, color, resolution)
    full_image = fullComposite(layer0, layer1, layer2, layer3, layer4)
    images_to_encode = [full_image, layer0, layer1, layer2, layer3, layer4]
    with ThreadPoolExecutor() as executor:
        encoded_images = list(executor.map(encodeImage, images_to_encode))
    return JSONResponse(content=encoded_images)

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
