"""Rebuild a catalog-ready image on a clean white square canvas."""

from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageEnhance, ImageOps


def rebuild_catalog_image(
    bg_removed_path: str | Path,
    output_path: str | Path,
    canvas_size: int = 1000,
    quality: dict[str, Any] | None = None,
) -> str:
    canvas_size = canvas_size if canvas_size in {125, 250, 500, 1000} else 1000
    product_box = int(canvas_size * 0.92)
    output = Path(output_path)

    with Image.open(bg_removed_path) as product:
        product = ImageOps.exif_transpose(product).convert("RGBA")
        product = _crop_to_subject(product)
        product = _enhance_product(product, quality or {})
        product.thumbnail((product_box, product_box), Image.LANCZOS)

        canvas = Image.new("RGBA", (canvas_size, canvas_size), (255, 255, 255, 255))
        x = (canvas_size - product.width) // 2
        y = (canvas_size - product.height) // 2
        canvas.alpha_composite(product, (x, y))
        canvas.convert("RGB").save(output, "PNG", optimize=True)

    return str(output)


def _crop_to_subject(product: Image.Image) -> Image.Image:
    """Crop transparent or white padding before resizing the product."""
    alpha = product.getchannel("A")
    bbox = _useful_alpha_bbox(alpha, product.size)
    if not bbox:
        bbox = _non_white_bbox(product)
    if bbox:
        return product.crop(_pad_bbox(bbox, product.size, max(2, int(max(product.size) * 0.015))))
    return product


def _useful_alpha_bbox(alpha: Image.Image, image_size: tuple[int, int]) -> tuple[int, int, int, int] | None:
    """Use alpha crop only when it actually removes meaningful canvas."""
    bbox = alpha.getbbox()
    if not bbox:
        return None

    image_area = image_size[0] * image_size[1]
    bbox_area = max(1, (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]))
    # rembg failure fallback is usually a fully opaque original, so the alpha bbox is the full image.
    if bbox_area / max(image_area, 1) > 0.92:
        return None
    return bbox


def _non_white_bbox(product: Image.Image) -> tuple[int, int, int, int] | None:
    """Find product bounds on images that still have a white/near-white background."""
    rgb = np.asarray(product.convert("RGB")).astype(np.int16)
    alpha = np.asarray(product.getchannel("A"))

    # Product pixels are usually darker or more saturated than a white catalog background.
    min_channel = rgb.min(axis=2)
    max_channel = rgb.max(axis=2)
    saturation = max_channel - min_channel
    non_white = ((min_channel < 242) | (saturation > 18)) & (alpha > 8)

    # Ignore tiny noise by requiring rows/columns to contain a small but real amount of subject.
    height, width = non_white.shape
    row_threshold = max(2, int(width * 0.006))
    col_threshold = max(2, int(height * 0.006))
    rows = np.where(non_white.sum(axis=1) >= row_threshold)[0]
    cols = np.where(non_white.sum(axis=0) >= col_threshold)[0]
    if rows.size == 0 or cols.size == 0:
        return None

    return int(cols[0]), int(rows[0]), int(cols[-1] + 1), int(rows[-1] + 1)


def _enhance_product(product: Image.Image, quality: dict[str, Any]) -> Image.Image:
    """Apply conservative catalog corrections based on measured quality issues."""
    alpha = product.getchannel("A")
    rgb = product.convert("RGB")

    brightness = quality.get("brightness")
    contrast = quality.get("contrast")
    blur_score = quality.get("blur_score")

    if isinstance(brightness, (int, float)):
        if brightness < 80:
            rgb = ImageEnhance.Brightness(rgb).enhance(min(1.28, 80 / max(brightness, 1)))
        elif brightness > 220:
            rgb = ImageEnhance.Brightness(rgb).enhance(max(0.82, 220 / max(brightness, 1)))

    if isinstance(contrast, (int, float)) and contrast < 35:
        rgb = ImageEnhance.Contrast(rgb).enhance(min(1.35, 35 / max(contrast, 1)))
    else:
        rgb = ImageEnhance.Contrast(rgb).enhance(1.05)

    if isinstance(blur_score, (int, float)) and blur_score < 80:
        rgb = ImageEnhance.Sharpness(rgb).enhance(1.35)

    enhanced = rgb.convert("RGBA")
    enhanced.putalpha(alpha)
    return enhanced


def _pad_bbox(bbox: tuple[int, int, int, int], image_size: tuple[int, int], padding: int) -> tuple[int, int, int, int]:
    left, top, right, bottom = bbox
    width, height = image_size
    return (
        max(0, left - padding),
        max(0, top - padding),
        min(width, right + padding),
        min(height, bottom + padding),
    )
