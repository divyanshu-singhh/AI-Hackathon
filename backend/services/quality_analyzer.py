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
