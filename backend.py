import os
import base64
import json

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from google import genai


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. "
        "Add it to Render Environment Variables."
    )


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="ShopMore API",
    description="AI product identification backend for ShopMore",
    version="2.0.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return FileResponse("index.html")


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "online",
        "message": "ShopMore backend is running!"
    }


# ============================================================
# STATIC FILES
# ============================================================

@app.get("/style.css")
def style():

    return FileResponse("style.css")


@app.get("/script.js")
def script():

    return FileResponse("script.js")


# ============================================================
# IMAGE ANALYSIS
# ============================================================

@app.post("/analyze-image")
async def analyze_image(
    file: UploadFile = File(...)
):

    # --------------------------------------------------------
    # CHECK FILE TYPE
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # READ IMAGE
    # --------------------------------------------------------

    image_bytes = await file.read()


    if not image_bytes:

        raise HTTPException(
            status_code=400,
            detail="The uploaded image is empty."
        )


    # --------------------------------------------------------
    # CONVERT IMAGE TO BASE64
    # --------------------------------------------------------

    image_base64 = base64.b64encode(
        image_bytes
    ).decode("utf-8")


    # --------------------------------------------------------
    # PROMPT
    # --------------------------------------------------------

    prompt = """
You are the product identification engine for ShopMore.

Analyze the uploaded product image carefully.

Identify the product as accurately as possible.

Look for:

- Brand
- Product name
- Model number
- Category
- Variant
- Color
- Visible specifications
- Text visible on the product or packaging

IMPORTANT:

Do NOT invent a model number or specification.

If something cannot be identified from the image,
leave that field empty.

Create a useful shopping search query that can be
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
"""


    # --------------------------------------------------------
    # SEND IMAGE TO GEMINI
    # --------------------------------------------------------

    try:

        response = client.models.generate_content(

            model="gemini-2.5-flash",

            contents=[
                {
                    "inline_data": {
                        "mime_type": file.content_type,
                        "data": image_base64
                    }
                },
                prompt
            ]
        )


        # ----------------------------------------------------
        # GET GEMINI RESPONSE
        # ----------------------------------------------------

        ai_result = response.text


        # ----------------------------------------------------
        # CLEAN POSSIBLE MARKDOWN
        # ----------------------------------------------------

        ai_result = ai_result.strip()


        if ai_result.startswith("```json"):

            ai_result = ai_result[
                7:
            ].strip()


        if ai_result.startswith("```"):

            ai_result = ai_result[
                3:
            ].strip()


        if ai_result.endswith("```"):

            ai_result = ai_result[
                :-3
            ].strip()


        # ----------------------------------------------------
        # VALIDATE JSON
        # ----------------------------------------------------

        try:

            parsed_result = json.loads(
                ai_result
            )

        except json.JSONDecodeError:

            parsed_result = {
                "brand": "",
                "product_name": "",
                "model": "",
                "category": "",
                "variant": "",
                "color": "",
                "search_query": ai_result,
                "confidence": 0
            }


        # ----------------------------------------------------
        # RETURN TO FRONTEND
        # ----------------------------------------------------

        return {

            "success": True,

            "filename":
                file.filename,

            "content_type":
                file.content_type,

            "analysis":
                json.dumps(
                    parsed_result
                )

        }


    except Exception as error:

        print(
            "GEMINI ERROR:",
            error
        )


        raise HTTPException(

            status_code=500,

            detail=
                f"AI analysis failed: {str(error)}"

        )
