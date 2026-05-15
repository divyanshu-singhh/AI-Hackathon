"""Vision LLM agent for product image understanding."""

from pathlib import Path
from typing import Any

from config import VISION_MODEL
from services.llm_client import chat_completion, image_to_data_url

VISION_PROMPT = """You are an expert product image parser for an ecommerce/catalog platform.

Analyze the uploaded product image.

Return ONLY valid JSON in this exact structure:

{
  "main_product": "",
  "detected_objects": [],
  "visible_text": "",
  "probable_category": "",
  "attributes": {
    "color": [],
    "material": [],
    "shape": "",
    "brand_or_label": "",
    "packaging": ""
  },
  "image_observations": [],
  "confidence": 0.0
}

Rules:
- Do not include markdown.
- Do not include explanation outside JSON.
- If text is not visible, use empty string.
- Do not invent brand names.
- detected_objects should include only visible objects.
- confidence should be from 0 to 1.
"""


def analyze_image(image_path: str | Path) -> dict[str, Any]:
    data_url = image_to_data_url(image_path)
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": VISION_PROMPT},
                {"type": "image_url", "image_url": {"url": data_url}},
            ],
        }
    ]
    result = chat_completion(VISION_MODEL, messages, temperature=0.1, max_tokens=1200)
    llm_meta = result.pop("_llm_meta", {})
    result.pop("_raw_gateway_response", None)
    if result.get("parse_error"):
        raise RuntimeError(f"Vision model returned invalid JSON: {result.get('parse_error')}")
    normalized = _normalize_vision_result(result)
    normalized["_llm_meta"] = llm_meta
    return normalized


def fallback_image_analysis(file_name: str, error: str) -> dict[str, Any]:
    guessed = Path(file_name).stem.replace("_", " ").replace("-", " ").strip()
    return {
        "main_product": guessed or "Unknown product",
        "detected_objects": [guessed] if guessed else [],
        "visible_text": "",
        "probable_category": "Uncategorized",
        "attributes": {"color": [], "material": [], "shape": "", "brand_or_label": "", "packaging": ""},
        "image_observations": ["LLM analysis failed; fallback result used."],
        "confidence": 0.0,
        "error": error,
    }


def _normalize_vision_result(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "main_product": result.get("main_product", "") or "",
        "detected_objects": _as_list(result.get("detected_objects", [])),
        "visible_text": result.get("visible_text", "") or "",
        "probable_category": result.get("probable_category", "") or "Uncategorized",
        "attributes": result.get("attributes", {}) if isinstance(result.get("attributes", {}), dict) else {},
        "image_observations": _as_list(result.get("image_observations", [])),
        "confidence": float(result.get("confidence", 0) or 0),
    }


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if value:
        return [str(value)]
    return []
