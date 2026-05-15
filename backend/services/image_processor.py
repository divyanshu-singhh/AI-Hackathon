"""File validation, upload saving, resizing, and remote-image download helpers."""

import shutil
import uuid
from pathlib import Path

import requests
from fastapi import UploadFile
from PIL import Image, ImageOps

from config import ALLOWED_EXTENSIONS, MAX_IMAGE_SIZE_MB, TEMP_DIR, UPLOAD_DIR


def validate_image_path(path: str | Path) -> None:
    image_path = Path(path)
    if image_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type. Use jpg, jpeg, png, or webp.")
    if image_path.stat().st_size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise ValueError(f"Image is larger than {MAX_IMAGE_SIZE_MB} MB.")


async def save_upload_file(upload: UploadFile) -> Path:
    suffix = Path(upload.filename or "upload.jpg").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type. Use jpg, jpeg, png, or webp.")

    temp_path = TEMP_DIR / f"{uuid.uuid4()}{suffix}"
    with temp_path.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)
    validate_image_path(temp_path)
    return temp_path


def copy_to_uploads(source_path: str | Path, image_id: str, original_filename: str) -> Path:
    source = Path(source_path)
    suffix = source.suffix.lower() if source.suffix.lower() in ALLOWED_EXTENSIONS else ".jpg"
    output_path = UPLOAD_DIR / f"{image_id}_original{suffix}"
    shutil.copy2(source, output_path)
    return output_path


def resize_for_llm(source_path: str | Path, image_id: str, max_dimension: int = 1024) -> Path:
    """Create a compressed RGB copy so large originals are not sent to the vision model."""
    source = Path(source_path)
    output_path = TEMP_DIR / f"{image_id}_llm.jpg"
    with Image.open(source) as img:
        img = ImageOps.exif_transpose(img).convert("RGB")
        img.thumbnail((max_dimension, max_dimension))
        img.save(output_path, "JPEG", quality=85, optimize=True)
    return output_path


def normalize_image(source_path: str | Path, image_id: str) -> Path:
    """Normalize orientation and mode for downstream OpenCV/Pillow operations."""
    source = Path(source_path)
    output_path = TEMP_DIR / f"{image_id}_normalized.png"
    with Image.open(source) as img:
        img = ImageOps.exif_transpose(img).convert("RGBA")
        img.save(output_path, "PNG")
    return output_path


def download_image(image_url: str, image_name: str | None = None) -> Path:
    response = requests.get(image_url, timeout=45, stream=True)
    response.raise_for_status()

    content_type = response.headers.get("content-type", "")
    suffix = Path(image_name or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        if "png" in content_type:
            suffix = ".png"
        elif "webp" in content_type:
            suffix = ".webp"
        else:
            suffix = ".jpg"

    output_path = TEMP_DIR / f"{uuid.uuid4()}{suffix}"
    with output_path.open("wb") as file:
        for chunk in response.iter_content(chunk_size=1024 * 512):
            if chunk:
                file.write(chunk)
    validate_image_path(output_path)
    return output_path
