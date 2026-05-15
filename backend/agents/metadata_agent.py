"""Text LLM agent for catalog metadata generation with deterministic fallback."""

import json
from typing import Any

from config import FALLBACK_TEXT_MODEL, TEXT_MODEL
from services.llm_client import chat_completion

METADATA_PROMPT = """You are a product catalog metadata expert.

Given:
1. Vision analysis JSON
2. OpenCV quality analysis JSON
3. Optional expected category

Generate clean catalog metadata.

Return ONLY valid JSON in this exact structure:

{
  "seo_title": "",
  "category": "",
  "tags": [],
  "search_keywords": [],
  "quality_label": "",
  "issues": [],
  "suggestions": [],
  "catalog_readiness_score": 0
}

Rules:
- Do not invent unavailable brand names.
- Keep SEO title short, useful, and searchable.
- Tags should be lowercase and practical.
- Suggestions should be actionable.
- catalog_readiness_score should be 0 to 100.
- If OCR text conflicts with object detection, mention it in issues.
"""


def generate_metadata(
    vision: dict[str, Any],
    quality: dict[str, Any],
    quality_summary: dict[str, Any],
    expected_category: str | None = None,
) -> dict[str, Any]:
    payload = {
        "vision_analysis": vision,
        "quality_analysis": quality,
        "quality_summary": quality_summary,
        "expected_category": expected_category,
    }
    messages = [
        {"role": "system", "content": METADATA_PROMPT},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]
    try:
        result = chat_completion(TEXT_MODEL, messages, temperature=0.2, max_tokens=900)
    except Exception:
        result = chat_completion(FALLBACK_TEXT_MODEL, messages, temperature=0.2, max_tokens=900)
    result.pop("_raw_gateway_response", None)
    return _normalize_metadata(result)


def fallback_metadata(
    vision: dict[str, Any],
    quality: dict[str, Any],
    quality_summary: dict[str, Any],
    expected_category: str | None,
    error: str,
) -> dict[str, Any]:
    main_product = vision.get("main_product") or "Product image"
    category = expected_category or vision.get("probable_category") or "Uncategorized"
    tags = sorted(
        {
            _clean_tag(main_product),
            _clean_tag(category),
            *[_clean_tag(item) for item in vision.get("detected_objects", [])],
        }
        - {""}
    )
    issues = [*quality_summary.get("issues", []), "LLM metadata failed; fallback result used."]
    suggestions = quality_summary.get("suggestions", []) or ["Review generated tags before catalog publishing."]
    return {
        "seo_title": main_product[:80],
        "category": category,
        "tags": tags,
        "search_keywords": tags,
        "quality_label": quality_summary.get("quality_label", ""),
        "issues": issues,
        "suggestions": suggestions,
        "catalog_readiness_score": int(quality.get("quality_score", 0) or 0),
        "error": error,
    }


def _normalize_metadata(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "seo_title": result.get("seo_title", "") or "",
        "category": result.get("category", "") or "Uncategorized",
        "tags": _as_list(result.get("tags", [])),
        "search_keywords": _as_list(result.get("search_keywords", [])),
        "quality_label": result.get("quality_label", "") or "",
        "issues": _as_list(result.get("issues", [])),
        "suggestions": _as_list(result.get("suggestions", [])),
        "catalog_readiness_score": int(result.get("catalog_readiness_score", 0) or 0),
    }


def _as_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if item]
    if value:
        return [str(value)]
    return []


def _clean_tag(value: str) -> str:
    return " ".join(str(value).lower().split())
