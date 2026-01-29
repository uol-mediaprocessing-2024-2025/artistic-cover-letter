import concurrent
from concurrent.futures import ThreadPoolExecutor
from PIL.Image import alpha_composite
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from backend.src.color_schemes import cluster_photos, get_image_colors
from backend.src.photo_analysis import getSubjects
from backend.src.image_processing import resizeImageShortest
from image_processing import calcDropshadow, calcBackgroundBleed, calcInnerShadow, \
    calcOutline, resizeImageLongest
from PIL import Image
from letter_rendering import generate_letter_layer, get_fonts
import io
import uvicorn
import base64
import os
import time


app = FastAPI()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (adjust for production use)
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# Analyzes photos and generates pairs with color values
@app.post("/analyze-photos")
async def analyze_photos(photos: list[UploadFile] = File(...)):
    starttime = time.time()
    images_hires = []
    print("Loading photos...")
    for photo in photos:
        data = await photo.read()
        image = Image.open(io.BytesIO(data))
        images_hires.append(image)
    with ThreadPoolExecutor() as executor:
        images = list(executor.map(resizeImageLongest, images_hires))
    print("Analyzing colors...")
    thread_count = max(int(os.cpu_count()/4),1)
    with ThreadPoolExecutor(max_workers=thread_count) as executor:
        photo_colors = list(executor.map(get_image_colors, images))
    schemes, groups = cluster_photos(photo_colors)
    content = []
    for scheme in schemes:
        content.append(scheme)
    for group in groups:
        content.append(group)
    endtime = time.time()
    print("Analysis took " + str(endtime - starttime) + " seconds")
    return JSONResponse(content=content)

# Generates text and effects
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

# Applies effects on an existing text layer
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
    # compress_level=1 offered a good balance between compression efficiency and encoding speed
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

# Retrieves installed fonts
@app.post("/retrieve-fonts")
async def retrieveFonts():
    font_files, font_names = get_fonts()
    return JSONResponse(content=font_names)

# Generates AI suggestions using the moondream AI model
@app.post("/generate-suggestions")
async def generateSuggestions(
        photos: list[UploadFile] = File(...)
):
    images = []
    for photo in photos:
        data = await photo.read()
        image = Image.open(io.BytesIO(data))
        image_scaled = resizeImageLongest(image, 512)
        images.append(image_scaled)
    results = getSubjects(images)
    return JSONResponse(content=results)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
