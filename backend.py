import os
import base64

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI


# --------------------------------------------------
# LOAD ENVIRONMENT VARIABLES
# --------------------------------------------------

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is missing. "
        "Please add it to your .env file."
    )


# --------------------------------------------------
# OPENAI CLIENT
# --------------------------------------------------

client = OpenAI(api_key=API_KEY)


# --------------------------------------------------
# CREATE FASTAPI APP
# --------------------------------------------------

app = FastAPI(
    title="ShopMore API",
    description="AI product identification backend for ShopMore",
    version="1.0.0"
)


# --------------------------------------------------
# CORS
# Allows the ShopMore frontend to communicate
# with this Python backend.
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# HOME / TEST ROUTE
# --------------------------------------------------

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "ShopMore backend is running!"
    }


# --------------------------------------------------
# IMAGE ANALYSIS
# --------------------------------------------------

@app.post("/analyze-image")
async def analyze_image(file: UploadFile = File(...)):

    # Check whether the uploaded file is an image
    if not file.content_type:
        raise HTTPException(
            status_code=400,
            detail="File type could not be detected."
        )

    if not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail="Please upload an image file."
        )


    # Read image
    image_bytes = await file.read()


    # Check empty image
    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="The uploaded image is empty."
        )


    # --------------------------------------------------
    # Convert image into Base64
    # --------------------------------------------------

    image_base64 = base64.b64encode(
        image_bytes
    ).decode("utf-8")


    # --------------------------------------------------
    # AI INSTRUCTIONS
    # --------------------------------------------------

    prompt = """
You are the product identification engine for ShopMore.

Analyze the uploaded product image carefully.

Your job is to identify the product as accurately as possible.

Look for:

- Brand
- Product name
- Model number
- Category
- Variant
- Color
- Visible specifications
- Any text visible on the product or packaging

IMPORTANT:

Do NOT invent a model number or specification.

If something cannot be identified from the image,
leave that field empty.

Create a useful shopping search query that could be
used to find this exact product online.

Return ONLY valid JSON.

Use exactly this structure:

{
    "brand": "",
    "product_name": "",
    "model": "",
    "category": "",
    "variant": "",
    "color": "",
    "search_query": "",
    "confidence": 0
}

The confidence value must be between 0 and 100.

Examples:

If the image contains Sony headphones:

{
    "brand": "Sony",
    "product_name": "WH-1000XM5",
    "model": "WH-1000XM5",
    "category": "Headphones",
    "variant": "Wireless Noise Cancelling",
    "color": "Black",
    "search_query": "Sony WH-1000XM5 Black Wireless Noise Cancelling Headphones",
    "confidence": 96
}

If the exact model cannot be determined,
identify the closest product possible and lower the confidence.
"""


    # --------------------------------------------------
    # SEND IMAGE TO AI
    # --------------------------------------------------

    try:

        response = client.responses.create(
            model="gpt-5.6",

            input=[
                {
                    "role": "user",

                    "content": [

                        {
                            "type": "input_text",
                            "text": prompt
                        },

                        {
                            "type": "input_image",
                            "image_url": (
                                f"data:{file.content_type};"
                                f"base64,{image_base64}"
                            )
                        }

                    ]
                }
            ]
        )


        # Get AI response
        ai_result = response.output_text


        # --------------------------------------------------
        # RETURN RESULT TO FRONTEND
        # --------------------------------------------------

        return {
            "success": True,
            "filename": file.filename,
            "content_type": file.content_type,
            "analysis": ai_result
        }


    except Exception as error:

        print("AI ERROR:", error)

        raise HTTPException(
            status_code=500,
            detail=f"AI analysis failed: {str(error)}"
        )


# --------------------------------------------------
# RUNNING NOTE
# --------------------------------------------------
#
# Start this server from the ShopMore folder with:
#
# uvicorn backend:app --reload
#
# Then open:
#
# http://127.0.0.1:8000
#
# --------------------------------------------------