"""Deterministic OpenCV quality scoring for product images."""

from pathlib import Path
from typing import Any

import cv2
import numpy as np


def analyze_quality(image_path: str | Path) -> dict[str, Any]:
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError("Unable to read image for quality analysis")

    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(np.mean(gray))
    contrast = float(np.std(gray))
    noise_score = _estimate_noise(gray)
    edge_density = _edge_density(gray)
    resolution_ok = width >= 600 and height >= 600
    aspect_ratio = round(width / height, 3) if height else 0

    issues: list[str] = []
    deductions: list[dict[str, Any]] = []
    score = 100

    if blur_score < 40:
        issues.append("Image appears blurry")
        deductions.append(_deduction("Blur", 25, f"Blur score {blur_score:.2f} is below 40", "Retake with sharper focus."))
        score -= 25
    elif blur_score < 80:
        issues.append("Image is slightly soft")
        deductions.append(_deduction("Blur", 12, f"Blur score {blur_score:.2f} is below 80", "Use a stable camera and better focus."))
        score -= 12

    if brightness < 80:
        issues.append("Image is underexposed")
        deductions.append(_deduction("Brightness", 15, f"Brightness {brightness:.2f} is below 80", "Increase lighting before capture."))
        score -= 15
    elif brightness > 220:
        issues.append("Image is overexposed")
        deductions.append(_deduction("Brightness", 15, f"Brightness {brightness:.2f} is above 220", "Reduce harsh light or reflections."))
        score -= 15

    if contrast < 35:
        issues.append("Low contrast")
        deductions.append(_deduction("Contrast", 12, f"Contrast {contrast:.2f} is below 35", "Use better lighting or a cleaner background."))
        score -= 12

    if not resolution_ok:
        issues.append("Resolution is below recommended 600x600")
        deductions.append(_deduction("Resolution", 18, f"Resolution is {width}x{height}", "Upload at least 600x600; 1000x1000 is better."))
        score -= 18

    if noise_score > 18:
        issues.append("Visible noise detected")
        deductions.append(_deduction("Noise", 10, f"Noise score {noise_score:.2f} is above 18", "Use brighter lighting or lower camera ISO."))
        score -= 10

    if edge_density > 0.18:
        issues.append("Background may be visually complex")
        deductions.append(_deduction("Background", 8, f"Background complexity {edge_density:.4f} is above 0.18", "Use a plain white or light gray background."))
        score -= 8

    if not deductions:
        issues.append("No measurable quality issues found")

    return {
        "width": width,
        "height": height,
        "blur_score": round(blur_score, 2),
        "brightness": round(brightness, 2),
        "contrast": round(contrast, 2),
        "noise_score": round(noise_score, 2),
        "resolution_ok": resolution_ok,
        "aspect_ratio": aspect_ratio,
        "background_complexity": round(edge_density, 4),
        "issues": issues,
        "deductions": deductions,
        "metric_guidance": {
            "blur_score": "Good: >= 80. Slightly soft: 40-79. Blurry: < 40.",
            "brightness": "Good: 80-220. Lower is underexposed; higher is overexposed.",
            "contrast": "Good: >= 35. Lower means product/background separation is weak.",
            "noise_score": "Good: <= 18. Higher means visible grain/noise.",
            "resolution": "Good: at least 600x600. Recommended: 1000x1000 or higher.",
            "background_complexity": "Good: <= 0.18. Higher means busy background or many edges.",
        },
        "quality_score": max(0, min(100, int(score))),
    }


def analyze_rebuilt_quality(image_path: str | Path) -> dict[str, Any]:
    """Score a rebuilt catalog image using product pixels, not the white canvas."""
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError("Unable to read rebuilt image for quality analysis")

    height, width = image.shape[:2]
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    subject_mask = _subject_mask(rgb)
    bbox = _mask_bbox(subject_mask)
    if bbox is None:
        fallback = analyze_quality(image_path)
        fallback["issues"] = ["Could not identify product area in rebuilt image", *fallback.get("issues", [])]
        fallback["quality_score"] = max(0, int(fallback.get("quality_score", 0)) - 20)
        return fallback

    left, top, right, bottom = bbox
    crop_gray = gray[top:bottom, left:right]
    product_gray = gray[subject_mask]
    blur_score = float(cv2.Laplacian(crop_gray, cv2.CV_64F).var())
    brightness = float(np.mean(product_gray))
    contrast = float(np.std(product_gray))
    noise_score = _estimate_noise(crop_gray)
    overexposed_ratio = float(np.count_nonzero(product_gray > 232) / max(product_gray.size, 1))
    product_fill = max(right - left, bottom - top) / max(min(width, height), 1)

    issues: list[str] = []
    deductions: list[dict[str, Any]] = []
    score = 100

    if blur_score < 35:
        issues.append("Rebuilt image appears blurry")
        deductions.append(_deduction("Rebuilt blur", 20, f"Blur score {blur_score:.2f} is below 35", "Use a sharper source image or reduce enlargement."))
        score -= 20
    elif blur_score < 65:
        issues.append("Rebuilt image is slightly soft")
        deductions.append(_deduction("Rebuilt blur", 10, f"Blur score {blur_score:.2f} is below 65", "Use a sharper source image."))
        score -= 10

    if brightness < 65:
        issues.append("Rebuilt product is underexposed")
        deductions.append(_deduction("Rebuilt brightness", 12, f"Product brightness {brightness:.2f} is below 65", "Increase product brightness slightly."))
        score -= 12
    elif brightness > 185 or overexposed_ratio > 0.08:
        issues.append("Rebuilt product is overexposed")
        deductions.append(_deduction("Rebuilt brightness", 18, f"Product brightness {brightness:.2f}, overexposed pixels {overexposed_ratio:.2%}", "Reduce rebuild brightness and preserve product detail."))
        score -= 18

    if contrast < 25:
        issues.append("Rebuilt product has low contrast")
        deductions.append(_deduction("Rebuilt contrast", 10, f"Product contrast {contrast:.2f} is below 25", "Improve contrast without washing out highlights."))
        score -= 10

    if noise_score > 18:
        issues.append("Visible noise remains in rebuilt image")
        deductions.append(_deduction("Rebuilt noise", 8, f"Noise score {noise_score:.2f} is above 18", "Apply denoise before sharpening."))
        score -= 8

    if product_fill < 0.72:
        issues.append("Rebuilt product leaves too much blank space")
        deductions.append(_deduction("Rebuilt layout", 18, f"Product fills {product_fill:.2%} of canvas", "Crop tighter and enlarge the product."))
        score -= 18
    elif product_fill > 0.98:
        issues.append("Rebuilt product is too close to the canvas edge")
        deductions.append(_deduction("Rebuilt layout", 8, f"Product fills {product_fill:.2%} of canvas", "Leave a small catalog margin."))
        score -= 8

    if not deductions:
        issues.append("No measurable rebuilt image issues found")

    return {
        "width": width,
        "height": height,
        "blur_score": round(blur_score, 2),
        "brightness": round(brightness, 2),
        "contrast": round(contrast, 2),
        "noise_score": round(noise_score, 2),
        "overexposed_ratio": round(overexposed_ratio, 4),
        "product_fill": round(product_fill, 4),
        "issues": issues,
        "deductions": deductions,
        "quality_score": max(0, min(100, int(score))),
    }


def _subject_mask(rgb: np.ndarray) -> np.ndarray:
    rgb_int = rgb.astype(np.int16)
    min_channel = rgb_int.min(axis=2)
    max_channel = rgb_int.max(axis=2)
    saturation = max_channel - min_channel
    mask = (min_channel < 242) | (saturation > 18)
    height, width = mask.shape
    row_threshold = max(2, int(width * 0.004))
    col_threshold = max(2, int(height * 0.004))
    rows = np.where(mask.sum(axis=1) >= row_threshold)[0]
    cols = np.where(mask.sum(axis=0) >= col_threshold)[0]
    if rows.size == 0 or cols.size == 0:
        return mask

    cleaned = np.zeros_like(mask)
    cleaned[rows[0] : rows[-1] + 1, cols[0] : cols[-1] + 1] = mask[rows[0] : rows[-1] + 1, cols[0] : cols[-1] + 1]
    return cleaned


def _mask_bbox(mask: np.ndarray) -> tuple[int, int, int, int] | None:
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    if rows.size == 0 or cols.size == 0:
        return None
    return int(cols[0]), int(rows[0]), int(cols[-1] + 1), int(rows[-1] + 1)


def _estimate_noise(gray: np.ndarray) -> float:
    median = cv2.medianBlur(gray, 3)
    diff = cv2.absdiff(gray, median)
    return float(np.std(diff))


def _edge_density(gray: np.ndarray) -> float:
    edges = cv2.Canny(gray, 100, 200)
    return float(np.count_nonzero(edges) / edges.size)


def _deduction(metric: str, points: int, reason: str, suggestion: str) -> dict[str, Any]:
    return {
        "metric": metric,
        "points": points,
        "reason": reason,
        "suggestion": suggestion,
    }
