import base64
import os
from io import BytesIO
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import Response
from openai import OpenAI

app = FastAPI(title="Face Fusion HD backend", version="1.0.0")

MAX_BYTES = 20 * 1024 * 1024
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


def get_client() -> OpenAI:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        raise HTTPException(status_code=503, detail="Server is not configured: OPENAI_API_KEY is missing.")
    return OpenAI(api_key=key, timeout=240.0, max_retries=1)


async def read_image(upload: UploadFile) -> bytes:
    if upload.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported image type: {upload.content_type}. Use JPG, PNG, or WEBP.")
    data = await upload.read()
    if not data:
        raise HTTPException(status_code=400, detail=f"{upload.filename or 'Image'} is empty.")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="Each image must be 20 MB or smaller.")
    return data


@app.get("/health")
def health():
    return {"ok": True, "service": "face-fusion-hd", "configured": bool(os.getenv("OPENAI_API_KEY"))}


@app.post("/v1/face-swap")
async def face_swap(
    source_image: Annotated[UploadFile, File(description="Photo whose facial identity should be used")],
    target_image: Annotated[UploadFile, File(description="Photo whose composition and body/background should be retained")],
):
    source_bytes = await read_image(source_image)
    target_bytes = await read_image(target_image)
    client = get_client()

    prompt = (
        "Perform a realistic, respectful face replacement using the two reference photographs. "
        "IMAGE 1 is the source identity reference: use the person's facial identity and recognizable facial features from image 1. "
        "IMAGE 2 is the target photograph: keep image 2 as the base and preserve its pose, expression as far as possible, hairstyle, "
        "clothing, body, camera angle, framing, background, lighting direction, and overall composition. "
        "Replace only the target person's face in image 2 with a natural-looking face matching the identity in image 1. "
        "Blend at the hairline, temples, cheeks, jaw, and neck with realistic skin texture, natural pores, sharp eyes and eyelashes, "
        "correct perspective, and consistent color temperature. Do not beautify excessively, do not smooth the skin into plastic, "
        "do not add text, watermarks, extra jewelry, or extra people. Return one photorealistic edited image, not a collage."
    )

    try:
        # Image API key remains on the server; never ship it in the Android APK.
        result = client.images.edit(
            model=os.getenv("OPENAI_IMAGE_MODEL", "gpt-image-2.5-sunburst"),
            image=[
                (source_image.filename or "source.jpg", BytesIO(source_bytes), source_image.content_type),
                (target_image.filename or "target.jpg", BytesIO(target_bytes), target_image.content_type),
            ],
            prompt=prompt,
            size="auto",
            quality="high",
            output_format="png",
            n=1,
        )
        if not result.data or not result.data[0].b64_json:
            raise HTTPException(status_code=502, detail="AI provider returned no image.")
        image_bytes = base64.b64decode(result.data[0].b64_json)
        return Response(content=image_bytes, media_type="image/png", headers={"Cache-Control": "no-store"})
    except HTTPException:
        raise
    except Exception as exc:
        # Avoid returning secrets or stack traces to the mobile client.
        print(f"Face swap provider error: {type(exc).__name__}: {exc}")
        raise HTTPException(status_code=502, detail=f"AI image edit failed ({type(exc).__name__}). Check server logs and API/model access.") from exc
