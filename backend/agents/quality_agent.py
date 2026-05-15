"""Human-friendly quality interpretation from deterministic metrics."""

from typing import Any


def summarize_quality(quality: dict[str, Any]) -> dict[str, Any]:
    score = int(quality.get("quality_score", 0) or 0)
    if score >= 85:
        label = "Excellent"
    elif score >= 70:
        label = "Good"
    elif score >= 50:
        label = "Average"
    else:
        label = "Poor"

    suggestions = []
    for issue in quality.get("issues", []):
        if "blurry" in issue.lower() or "soft" in issue.lower():
            suggestions.append("Retake the photo with a stable camera and better focus.")
        elif "underexposed" in issue.lower():
            suggestions.append("Increase lighting before capturing the product.")
        elif "overexposed" in issue.lower():
            suggestions.append("Reduce harsh light or reflections.")
        elif "contrast" in issue.lower():
            suggestions.append("Use a cleaner background and improve contrast.")
        elif "resolution" in issue.lower():
            suggestions.append("Upload a larger image, preferably at least 1000x1000.")
        elif "noise" in issue.lower():
            suggestions.append("Use brighter lighting or a lower camera ISO setting.")
        elif "complex" in issue.lower():
            suggestions.append("Use a plain white or light gray background.")

    return {"quality_label": label, "issues": quality.get("issues", []), "suggestions": suggestions}
