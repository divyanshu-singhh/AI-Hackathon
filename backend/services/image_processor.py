"""File validation, upload saving, resizing, and remote-image download helpers."""

import base64
import re
import shutil
import uuid
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlencode, urlparse

import requests
from fastapi import UploadFile
from PIL import Image, ImageOps

from config import ALLOWED_EXTENSIONS, MAX_IMAGE_SIZE_MB, TEMP_DIR, UPLOAD_DIR

DOWNLOAD_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
    "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
}


def validate_image_path(path: str | Path) -> None:
    image_path = Path(path)
    if image_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type. Use jpg, jpeg, png, or webp.")
    if image_path.stat().st_size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise ValueError(f"Image is larger than {MAX_IMAGE_SIZE_MB} MB.")
    try:
        with Image.open(image_path) as img:
            img.verify()
    except Exception as exc:
        raise ValueError(f"Downloaded file is not a readable image: {exc}") from exc


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
    cleaned_url = normalize_image_url(image_url)
    if not cleaned_url:
        raise ValueError("Image URL is empty")

    if cleaned_url.startswith("data:image/"):
        return _download_data_url(cleaned_url, image_name)

    if not cleaned_url.startswith(("http://", "https://")):
        raise ValueError("Image URL must start with http:// or https://")

    response = requests.get(
        cleaned_url,
        timeout=(12, 60),
        stream=True,
        allow_redirects=True,
        headers=DOWNLOAD_HEADERS,
    )
    response.raise_for_status()

    content_type = response.headers.get("content-type", "").lower()
    suffix = _choose_suffix(image_name, cleaned_url, content_type)
    output_path = TEMP_DIR / f"{uuid.uuid4()}{suffix}"

    max_bytes = MAX_IMAGE_SIZE_MB * 1024 * 1024
    downloaded = 0
    with output_path.open("wb") as file:
        for chunk in response.iter_content(chunk_size=1024 * 512):
            if not chunk:
                continue
            downloaded += len(chunk)
            if downloaded > max_bytes:
                output_path.unlink(missing_ok=True)
                raise ValueError(f"Remote image is larger than {MAX_IMAGE_SIZE_MB} MB")
            file.write(chunk)

    if downloaded == 0:
        output_path.unlink(missing_ok=True)
        raise ValueError("Remote image download returned an empty file")

    try:
        validate_image_path(output_path)
    except Exception as exc:
        preview = response.text[:160] if "text" in content_type or "html" in content_type else ""
        output_path.unlink(missing_ok=True)
        detail = f" URL returned content-type '{content_type}'." if content_type else ""
        if preview:
            detail += f" Response preview: {preview}"
        raise ValueError(f"Could not download a valid image from URL.{detail} {exc}") from exc
    return output_path


def normalize_image_url(raw_url: str) -> str:
    """Clean CSV/formula values into a direct URL where possible."""
    url = str(raw_url or "").strip()
    url = url.strip("'\"")
    if not url:
        return ""

    image_formula = re.search(r'=IMAGE\(\s*["\']([^"\']+)["\']', url, flags=re.IGNORECASE)
    if image_formula:
        url = image_formula.group(1)

    first_url = re.search(r"https?://[^\s,\"')]+", url)
    if first_url:
        url = first_url.group(0)

    if url.startswith("//"):
        url = f"https:{url}"
    if url.lower().startswith("www."):
        url = f"https://{url}"
    url = unquote(url.strip())
    return _normalize_google_drive_url(url)


def _download_data_url(data_url: str, image_name: str | None) -> Path:
    header, encoded = data_url.split(",", 1)
    suffix = ".png" if "png" in header.lower() else ".webp" if "webp" in header.lower() else ".jpg"
    suffix = Path(image_name or "").suffix.lower() if Path(image_name or "").suffix.lower() in ALLOWED_EXTENSIONS else suffix
    output_path = TEMP_DIR / f"{uuid.uuid4()}{suffix}"
    data = base64.b64decode(encoded)
    if len(data) > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise ValueError(f"Remote image is larger than {MAX_IMAGE_SIZE_MB} MB")
    output_path.write_bytes(data)
    validate_image_path(output_path)
    return output_path


def _choose_suffix(image_name: str | None, image_url: str, content_type: str) -> str:
    for candidate in (
        Path(image_name or "").suffix.lower(),
        Path(urlparse(image_url).path).suffix.lower(),
    ):
        if candidate in ALLOWED_EXTENSIONS:
            return candidate

    if "png" in content_type:
        return ".png"
    if "webp" in content_type:
        return ".webp"
    if "jpeg" in content_type or "jpg" in content_type:
        return ".jpg"
    return ".jpg"


def _normalize_google_drive_url(url: str) -> str:
    parsed = urlparse(url)
    if "drive.google.com" not in parsed.netloc:
        return url

    file_match = re.search(r"/file/d/([^/]+)", parsed.path)
    file_id = file_match.group(1) if file_match else parse_qs(parsed.query).get("id", [""])[0]
    if not file_id:
        return url
    return f"https://drive.google.com/uc?{urlencode({'export': 'download', 'id': file_id})}"
