"""Pipeline coordinator that runs only the frontend-selected processing stages."""

import uuid
from pathlib import Path
from typing import Any

from config import DEFAULT_STAGES, OUTPUT_DIR, storage_url
from agents.image_analysis_agent import analyze_image, fallback_image_analysis
from agents.metadata_agent import fallback_metadata, generate_metadata
from agents.quality_agent import summarize_quality
from services.background_remover import remove_background
from services.image_processor import copy_to_uploads, normalize_image, resize_for_llm, validate_image_path
from services.image_rebuilder import rebuild_catalog_image
from services.quality_analyzer import analyze_quality


def process_image(
    image_path: str | Path,
    original_filename: str,
    expected_category: str | None = None,
    stages: set[str] | None = None,
) -> dict[str, Any]:
    image_id = str(uuid.uuid4())
    selected_stages = stages or DEFAULT_STAGES
    result = _base_result(image_id, original_filename, selected_stages)

    try:
        validate_image_path(image_path)
        uploaded_path = copy_to_uploads(image_path, image_id, original_filename)
        normalized_path = normalize_image(uploaded_path, image_id)
        result["original_image_url"] = storage_url("uploads", uploaded_path.name)

        quality = {}
        quality_summary = {"quality_label": "", "issues": [], "suggestions": []}
        if "quality" in selected_stages:
            quality = analyze_quality(normalized_path)
            quality_summary = summarize_quality(quality)
            result["quality_score"] = quality.get("quality_score")
            result["quality_breakdown"] = quality
        else:
            result["issues"].append("Quality stage skipped by user.")

        bg_removed_path = normalized_path
        bg_warning = None
        if "background" in selected_stages:
            bg_output = OUTPUT_DIR / f"{image_id}_bg_removed.png"
            bg_removed_path, bg_warning = remove_background(normalized_path, bg_output)
            result["background_removed_image_url"] = storage_url("outputs", bg_output.name)
            if bg_warning:
                result["issues"].append("Background removal failed.")

        if "rebuild" in selected_stages:
            rebuilt_output = OUTPUT_DIR / f"{image_id}_rebuilt.png"
            rebuild_catalog_image(bg_removed_path, rebuilt_output)
            result["rebuilt_image_url"] = storage_url("outputs", rebuilt_output.name)

        vision = {}
        if "vision" in selected_stages:
            llm_image_path = resize_for_llm(uploaded_path, image_id)
            try:
                vision = analyze_image(llm_image_path)
            except Exception as exc:
                vision = fallback_image_analysis(original_filename, str(exc))
                result["issues"].append("LLM analysis failed; fallback result used.")
        else:
            result["issues"].append("Vision stage skipped by user.")

        metadata = {}
        if "metadata" in selected_stages:
            try:
                metadata = generate_metadata(vision, quality, quality_summary, expected_category)
            except Exception as exc:
                metadata = fallback_metadata(vision, quality, quality_summary, expected_category, str(exc))
                result["issues"].append("LLM metadata failed; fallback result used.")
        else:
            result["issues"].append("Metadata stage skipped by user.")

        _merge_result(result, vision, metadata, quality_summary, bg_warning)
        return result
    except Exception as exc:
        result["status"] = "failed"
        result["error"] = f"Unable to process image: {exc}"
        return result


def _base_result(image_id: str, file_name: str, stages: set[str]) -> dict[str, Any]:
    return {
        "image_id": image_id,
        "file_name": file_name,
        "status": "success",
        "selected_stages": sorted(stages),
        "original_image_url": None,
        "background_removed_image_url": None,
        "rebuilt_image_url": None,
        "detected_objects": [],
        "extracted_text": "",
        "main_product": "",
        "category": "Uncategorized",
        "tags": [],
        "seo_title": "",
        "quality_score": None,
        "quality_breakdown": {},
        "issues": [],
        "suggestions": [],
        "raw_llm_analysis": {},
        "error": None,
    }


def _merge_result(
    result: dict[str, Any],
    vision: dict[str, Any],
    metadata: dict[str, Any],
    quality_summary: dict[str, Any],
    bg_warning: str | None,
) -> None:
    result["raw_llm_analysis"] = vision
    result["main_product"] = vision.get("main_product", "")
    result["detected_objects"] = vision.get("detected_objects", [])
    result["extracted_text"] = vision.get("visible_text", "")
    result["category"] = metadata.get("category") or vision.get("probable_category") or "Uncategorized"
    result["tags"] = metadata.get("tags", [])
    result["seo_title"] = metadata.get("seo_title", "")

    issues = [
        *result.get("issues", []),
        *quality_summary.get("issues", []),
        *metadata.get("issues", []),
    ]
    if bg_warning:
        issues.append(bg_warning)
    result["issues"] = _dedupe(issues)
    result["suggestions"] = _dedupe([*quality_summary.get("suggestions", []), *metadata.get("suggestions", [])])


def _dedupe(items: list[Any]) -> list[str]:
    seen = set()
    output = []
    for item in items:
        text = str(item).strip()
        if text and text not in seen:
            seen.add(text)
            output.append(text)
    return output
