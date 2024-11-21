from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from image_processing import process_image_blur
import io
import uvicorn
import cv2
import numpy as np
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
@app.post("/submit-text")
async def submit_text(request: Request):
    text = await request.json();
    print(f"Received text: {text}")

    font = Font("/content/fonts/impact.ttf", 500)
    letter = Letter("D", font, 0, 0, 3)

    # draw the initial text
    text2 = LetterText(text, font, 0, 0)
    img = text2.draw()

    # draw the black and semi-transparent text
    img_black_trans = np.copy(img)
    for r in range(img_black_trans.shape[0]):
        for c in range(img_black_trans.shape[1]):
            img_black_trans[r][c][0] = 0
            img_black_trans[r][c][1] = 0
            img_black_trans[r][c][2] = 0

            old_alpha = img_black_trans[r][c][3]
            img_black_trans[r][c][3] = old_alpha * 0.5
    img_black_trans = cv2.blur(img_black_trans,(15,15),0)

    # draw a blurred version of the text image
    img_blurred = np.copy(img)
    img_blurred = cv2.blur(img_blurred,(30,30))

    final_img = np.zeros((img.shape[0],img.shape[1]*3,4),dtype=np.uint8)
    final_img = blend_images(img_blurred,img_black_trans)
    final_img = blend_images(final_img,img)

    img = final_img

    imgplot = plt.imshow(final_img)
    plt.show()

    image_io = io.BytesIO()
    img.save(image_io, format="PNG")
    image_io.seek(0)
    return StreamingResponse(image_io, media_type="image/png")


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
