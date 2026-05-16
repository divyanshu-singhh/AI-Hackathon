"""Rebuild a catalog-ready image on a clean white square canvas."""

from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps


PRODUCT_FILL_RATIO = 0.96


def rebuild_catalog_image(
    bg_removed_path: str | Path,
    output_path: str | Path,
    canvas_size: int = 1000,
    quality: dict[str, Any] | None = None,
) -> str:
    canvas_size = canvas_size if canvas_size in {125, 250, 500, 1000} else 1000
    product_box = int(canvas_size * PRODUCT_FILL_RATIO)
    output = Path(output_path)
    quality = quality or {}

    with Image.open(bg_removed_path) as product:
        product = ImageOps.exif_transpose(product).convert("RGBA")
        product = _apply_foreground_mask_if_needed(product, quality)
        product = _crop_to_subject(product)
        product = _enhance_product(product, quality)
        product = _resize_to_fit(product, product_box)
        product = _sharpen_after_resize(product, quality)

        canvas = Image.new("RGBA", (canvas_size, canvas_size), (255, 255, 255, 255))
        x = (canvas_size - product.width) // 2
        y = (canvas_size - product.height) // 2
        canvas.alpha_composite(product, (x, y))
        canvas.convert("RGB").save(output, "PNG", optimize=True)

    return str(output)


def _crop_to_subject(product: Image.Image) -> Image.Image:
    """Crop transparent or white padding before resizing the product."""
    alpha = product.getchannel("A")
    alpha_bbox = _useful_alpha_bbox(alpha, product.size)
    if alpha_bbox:
        return product.crop(_pad_bbox(alpha_bbox, product.size, 0))

    bbox = _non_white_bbox(product)
    if bbox:
        return product.crop(_pad_bbox(bbox, product.size, max(1, int(max(product.size) * 0.008))))
    return product


def _useful_alpha_bbox(alpha: Image.Image, image_size: tuple[int, int]) -> tuple[int, int, int, int] | None:
    """Use alpha crop only when it actually removes meaningful canvas."""
    mask = np.asarray(alpha) > 8
    bbox = _mask_bbox(mask)
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

    subject_stats = _subject_stats(rgb, alpha)
    brightness = subject_stats.get("brightness", quality.get("brightness"))
    contrast = subject_stats.get("contrast", quality.get("contrast"))
    overexposed_ratio = subject_stats.get("overexposed_ratio", 0)
    blur_score = quality.get("blur_score")
    noise_score = quality.get("noise_score")
    issues = " ".join(quality.get("issues", [])).lower()

    if isinstance(noise_score, (int, float)) and noise_score > 18:
        denoised = rgb.filter(ImageFilter.MedianFilter(size=3))
        rgb = Image.blend(rgb, denoised, 0.55)

    if isinstance(brightness, (int, float)):
        if brightness < 70 and overexposed_ratio < 0.03:
            factor = min(1.18, max(1.03, 92 / max(brightness, 1)))
            rgb = ImageEnhance.Brightness(rgb).enhance(factor)
        elif brightness > 168 or overexposed_ratio > 0.08:
            factor = max(0.82, min(0.97, 145 / max(brightness, 1)))
            rgb = ImageEnhance.Brightness(rgb).enhance(factor)

    if isinstance(contrast, (int, float)) and contrast < 35:
        rgb = ImageEnhance.Contrast(rgb).enhance(min(1.22, max(1.05, 38 / max(contrast, 1))))
    else:
        rgb = ImageEnhance.Contrast(rgb).enhance(1.02)

    if isinstance(blur_score, (int, float)):
        if blur_score < 40:
            rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.6, percent=170, threshold=3))
        elif blur_score < 80:
            rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.2, percent=125, threshold=3))
    elif "blurry" in issues or "soft" in issues:
        rgb = ImageEnhance.Sharpness(rgb).enhance(1.25)

    enhanced = rgb.convert("RGBA")
    enhanced.putalpha(alpha)
    return enhanced


def _subject_stats(rgb: Image.Image, alpha: Image.Image) -> dict[str, float]:
    """Measure the visible product, excluding transparent and near-white canvas pixels."""
    rgb_array = np.asarray(rgb).astype(np.int16)
    alpha_array = np.asarray(alpha)
    min_channel = rgb_array.min(axis=2)
    max_channel = rgb_array.max(axis=2)
    saturation = max_channel - min_channel
    subject_mask = (alpha_array > 24) & ((min_channel < 240) | (saturation > 20))
    if np.count_nonzero(subject_mask) < 25:
        subject_mask = alpha_array > 24
    if np.count_nonzero(subject_mask) < 25:
        return {}

    gray = np.asarray(rgb.convert("L")).astype(np.float32)
    subject_gray = gray[subject_mask]
    return {
        "brightness": float(np.mean(subject_gray)),
        "contrast": float(np.std(subject_gray)),
        "overexposed_ratio": float(np.count_nonzero(subject_gray > 232) / max(subject_gray.size, 1)),
    }


def _resize_to_fit(product: Image.Image, product_box: int) -> Image.Image:
    """Resize up or down so the product fills the catalog canvas."""
    width, height = product.size
    longest_side = max(width, height)
    if longest_side <= 0:
        return product

    scale = product_box / longest_side
    new_size = (
        max(1, int(round(width * scale))),
        max(1, int(round(height * scale))),
    )
    if new_size == product.size:
        return product
    return product.resize(new_size, Image.LANCZOS)


def _sharpen_after_resize(product: Image.Image, quality: dict[str, Any]) -> Image.Image:
    """Recover a little edge crispness after enlargement or blur correction."""
    blur_score = quality.get("blur_score")
    resolution_ok = quality.get("resolution_ok")
    if resolution_ok is True and not (isinstance(blur_score, (int, float)) and blur_score < 80):
        return product

    alpha = product.getchannel("A")
    rgb = product.convert("RGB")
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.0, percent=115, threshold=4))
    sharpened = rgb.convert("RGBA")
    sharpened.putalpha(alpha)
    return sharpened


def _apply_foreground_mask_if_needed(product: Image.Image, quality: dict[str, Any]) -> Image.Image:
    """Use OpenCV foreground estimation when background removal returned a full opaque image."""
    alpha = np.asarray(product.getchannel("A"))
    opaque_ratio = float(np.count_nonzero(alpha > 8) / max(alpha.size, 1))
    if opaque_ratio < 0.94:
        return product

    background_complexity = quality.get("background_complexity")
    issues = " ".join(quality.get("issues", [])).lower()
    should_try_mask = (
        (isinstance(background_complexity, (int, float)) and background_complexity > 0.18)
        or "background" in issues
        or _non_white_bbox(product) is None
    )
    if not should_try_mask:
        return product

    mask = _grabcut_subject_mask(product)
    if mask is None:
        return product

    alpha_image = Image.fromarray(mask, mode="L").filter(ImageFilter.GaussianBlur(radius=0.6))
    masked = product.copy()
    masked.putalpha(alpha_image)
    return masked


def _grabcut_subject_mask(product: Image.Image) -> np.ndarray | None:
    rgb = np.asarray(product.convert("RGB"))
    height, width = rgb.shape[:2]
    if width < 40 or height < 40:
        return None

    margin_x = max(2, int(width * 0.04))
    margin_y = max(2, int(height * 0.04))
    rect = (margin_x, margin_y, width - 2 * margin_x, height - 2 * margin_y)
    if rect[2] <= 1 or rect[3] <= 1:
        return None

    mask = np.zeros((height, width), np.uint8)
    bg_model = np.zeros((1, 65), np.float64)
    fg_model = np.zeros((1, 65), np.float64)
    try:
        cv2.grabCut(rgb, mask, rect, bg_model, fg_model, 4, cv2.GC_INIT_WITH_RECT)
    except cv2.error:
        return None

    foreground = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype("uint8")
    foreground_ratio = float(np.count_nonzero(foreground) / max(foreground.size, 1))
    if foreground_ratio < 0.03 or foreground_ratio > 0.9:
        return None

    kernel_size = max(3, int(min(width, height) * 0.01))
    if kernel_size % 2 == 0:
        kernel_size += 1
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    foreground = cv2.morphologyEx(foreground, cv2.MORPH_OPEN, kernel)
    foreground = cv2.morphologyEx(foreground, cv2.MORPH_CLOSE, kernel)
    return foreground


def _mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    if rows.size == 0 or cols.size == 0:
        return None
    return int(cols[0]), int(rows[0]), int(cols[-1] + 1), int(rows[-1] + 1)


def _pad_bbox(bbox: tuple[int, int, int, int], image_size: tuple[int, int], padding: int) -> tuple[int, int, int, int]:
    left, top, right, bottom = bbox
    width, height = image_size
    return (
        max(0, left - padding),
        max(0, top - padding),
        min(width, right + padding),
        min(height, bottom + padding),
    )
