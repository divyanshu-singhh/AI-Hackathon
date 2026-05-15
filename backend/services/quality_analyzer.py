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
    score = 100

    if blur_score < 40:
        issues.append("Image appears blurry")
        score -= 25
    elif blur_score < 80:
        issues.append("Image is slightly soft")
        score -= 12

    if brightness < 80:
        issues.append("Image is underexposed")
        score -= 15
    elif brightness > 220:
        issues.append("Image is overexposed")
        score -= 15

    if contrast < 35:
        issues.append("Low contrast")
        score -= 12

    if not resolution_ok:
        issues.append("Resolution is below recommended 600x600")
        score -= 18

    if noise_score > 18:
        issues.append("Visible noise detected")
        score -= 10

    if edge_density > 0.18:
        issues.append("Background may be visually complex")
        score -= 8

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
        "quality_score": max(0, min(100, int(score))),
    }


def _estimate_noise(gray: np.ndarray) -> float:
    median = cv2.medianBlur(gray, 3)
    diff = cv2.absdiff(gray, median)
    return float(np.std(diff))


def _edge_density(gray: np.ndarray) -> float:
    edges = cv2.Canny(gray, 100, 200)
    return float(np.count_nonzero(edges) / edges.size)
