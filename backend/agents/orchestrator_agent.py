"""Pipeline coordinator that runs only the frontend-selected processing stages."""

import uuid
from pathlib import Path
from typing import Any

from config import DEFAULT_STAGES, OUTPUT_DIR, TEXT_MODEL, VISION_MODEL, storage_url
from agents.image_analysis_agent import analyze_image, extract_ocr_text, fallback_image_analysis
from agents.metadata_agent import fallback_metadata, generate_metadata
from agents.quality_agent import summarize_quality
from services.background_remover import remove_background
from services.cost_utils import format_cost, parse_cost
from services.image_processor import copy_to_uploads, normalize_image, resize_for_llm, validate_image_path
from services.image_rebuilder import rebuild_catalog_image
from services.progress_manager import model_type_for, progress_manager
from services.quality_analyzer import analyze_quality, analyze_rebuilt_quality

LOCAL_STAGE_META = {
    "validate": ("Validate & Save", "Python/Pillow", "Open source local tool"),
    "quality": ("Check Image Quality", "OpenCV", "Open source local tool"),
    "background": ("Remove Background", "rembg U2-Net", "Open source local tool"),
    "rebuild": ("Create Final Image", "Pillow", "Open source local tool"),
    "ocr": ("Read Text from Image", VISION_MODEL, model_type_for(VISION_MODEL)),
    "vision": ("Identify Product", VISION_MODEL, model_type_for(VISION_MODEL)),
    "metadata": ("Create Title & Tags", TEXT_MODEL, model_type_for(TEXT_MODEL)),
    "finalize": ("Finalize Result", "FastAPI", "Open source local tool"),
}

STAGE_PERCENT = {
    "validate": (3, 12),
    "quality": (12, 28),
    "background": (28, 48),
    "rebuild": (48, 62),
    "ocr": (62, 74),
    "vision": (74, 86),
    "metadata": (86, 96),
    "finalize": (96, 100),
}


def process_image(
    image_path: str | Path,
    original_filename: str,
    expected_category: str | None = None,
    stages: set[str] | None = None,
    progress_job_id: str | None = None,
    crop_size: int = 1000,
) -> dict[str, Any]:
    image_id = str(uuid.uuid4())
    selected_stages = stages or DEFAULT_STAGES
    result = _base_result(image_id, original_filename, selected_stages)

    try:
        _emit_stage(progress_job_id, "validate", "running", message=f"Preparing {original_filename}")
        validate_image_path(image_path)
        uploaded_path = copy_to_uploads(image_path, image_id, original_filename)
        normalized_path = normalize_image(uploaded_path, image_id)
        result["original_image_url"] = storage_url("uploads", uploaded_path.name)
        _emit_stage(progress_job_id, "validate", "completed", message="Image validated and saved")

        quality = {}
        quality_summary = {"quality_label": "", "issues": [], "suggestions": []}
        if "quality" in selected_stages:
            _emit_stage(progress_job_id, "quality", "running", message="Calculating blur, brightness, contrast, noise, and resolution")
            quality = analyze_quality(normalized_path)
            quality_summary = summarize_quality(quality)
            result["quality_score"] = quality.get("quality_score")
            result["quality_breakdown"] = quality
            _emit_stage(progress_job_id, "quality", "completed", message=f"Quality score: {quality.get('quality_score', 'N/A')}")
        else:
            result["issues"].append("Quality stage skipped by user.")
            _emit_stage(progress_job_id, "quality", "skipped", message="Skipped by user")

        bg_removed_path = normalized_path
        bg_warning = None
        if "background" in selected_stages:
            _emit_stage(progress_job_id, "background", "running", message="Removing image background")
            bg_output = OUTPUT_DIR / f"{image_id}_bg_removed.png"
            bg_removed_path, bg_warning = remove_background(normalized_path, bg_output)
            result["background_removed_image_url"] = storage_url("outputs", bg_output.name)
            if bg_warning:
                result["issues"].append("Background removal failed.")
                _emit_stage(progress_job_id, "background", "failed", message="Background removal failed; original image copied")
            else:
                _emit_stage(progress_job_id, "background", "completed", message="Background removed")
        else:
            _emit_stage(progress_job_id, "background", "skipped", message="Skipped by user")

        if "rebuild" in selected_stages:
            _emit_stage(progress_job_id, "rebuild", "running", message=f"Building {crop_size}x{crop_size} clean catalog image")
            rebuilt_output = OUTPUT_DIR / f"{image_id}_rebuilt.png"
            rebuild_catalog_image(bg_removed_path, rebuilt_output, crop_size, quality)
            result["rebuilt_image_url"] = storage_url("outputs", rebuilt_output.name)
            result["crop_size"] = crop_size
            try:
                rebuilt_quality = analyze_rebuilt_quality(rebuilt_output)
                result["rebuilt_quality_score"] = rebuilt_quality.get("quality_score")
                result["rebuilt_quality_breakdown"] = rebuilt_quality
            except Exception as exc:
                result["issues"].append(f"Final image quality check failed: {exc}")
            _emit_stage(progress_job_id, "rebuild", "completed", message="Catalog image rebuilt")
        else:
            _emit_stage(progress_job_id, "rebuild", "skipped", message="Skipped by user")

        vision = {}
        ocr = {}
        if "ocr" in selected_stages:
            _emit_stage(progress_job_id, "ocr", "running", message="Reading visible product text")
            llm_image_path = resize_for_llm(uploaded_path, image_id)
            try:
                ocr = extract_ocr_text(llm_image_path)
                _add_llm_usage(result, ocr.get("_llm_meta", {}))
                result["extracted_text"] = ocr.get("extracted_text", "")
                result["ocr_text_blocks"] = ocr.get("text_blocks", [])
                _emit_stage(
                    progress_job_id,
                    "ocr",
                    "completed",
                    message="OCR text detection complete",
                    llm_meta=ocr.get("_llm_meta", {}),
                )
            except Exception as exc:
                result["issues"].append("OCR text detection failed.")
                _emit_stage(progress_job_id, "ocr", "failed", message=str(exc))
        else:
            _emit_stage(progress_job_id, "ocr", "skipped", message="Skipped by user")

        if "vision" in selected_stages:
            _emit_stage(progress_job_id, "vision", "running", message="Identifying the product and visible details")
            llm_image_path = resize_for_llm(uploaded_path, image_id)
            try:
                vision = analyze_image(llm_image_path)
                _add_llm_usage(result, vision.get("_llm_meta", {}))
                if result.get("extracted_text"):
                    vision["visible_text"] = result["extracted_text"]
                _emit_stage(
                    progress_job_id,
                    "vision",
                    "completed",
                    message="Product details identified",
                    llm_meta=vision.get("_llm_meta", {}),
                )
            except Exception as exc:
                vision = fallback_image_analysis(original_filename, str(exc))
                result["issues"].append("LLM analysis failed; fallback result used.")
                _emit_stage(progress_job_id, "vision", "failed", message=str(exc))
        else:
            result["issues"].append("Identify Product stage skipped by user.")
            _emit_stage(progress_job_id, "vision", "skipped", message="Skipped by user")

        if result.get("extracted_text") and not vision.get("visible_text"):
            vision["visible_text"] = result["extracted_text"]

        metadata = {}
        if "metadata" in selected_stages:
            _emit_stage(progress_job_id, "metadata", "running", message="Creating product title, tags, and catalog suggestions")
            try:
                metadata = generate_metadata(vision, quality, quality_summary, expected_category)
                _add_llm_usage(result, metadata.get("_llm_meta", {}))
                _emit_stage(
                    progress_job_id,
                    "metadata",
                    "completed",
                    message="Title and tags created",
                    llm_meta=metadata.get("_llm_meta", {}),
                )
            except Exception as exc:
                metadata = fallback_metadata(vision, quality, quality_summary, expected_category, str(exc))
                result["issues"].append("LLM metadata failed; fallback result used.")
                _emit_stage(progress_job_id, "metadata", "failed", message=str(exc))
        else:
            result["issues"].append("Create Title & Tags stage skipped by user.")
            _emit_stage(progress_job_id, "metadata", "skipped", message="Skipped by user")

        _emit_stage(progress_job_id, "finalize", "running", message="Combining image outputs and metadata")
        _merge_result(result, vision, metadata, quality_summary, bg_warning)
        _emit_stage(progress_job_id, "finalize", "completed", message="Processing complete")
        return result
    except Exception as exc:
        result["status"] = "failed"
        result["error"] = f"Unable to process image: {exc}"
        _emit_stage(progress_job_id, "finalize", "failed", message=result["error"])
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
        "ocr_text_blocks": [],
        "main_product": "",
        "category": "Uncategorized",
        "tags": [],
        "seo_title": "",
        "product_name_suggestions": [],
        "quality_score": None,
        "quality_breakdown": {},
        "rebuilt_quality_score": None,
        "rebuilt_quality_breakdown": {},
        "llm_cost": 0.0,
        "llm_cost_display": "",
        "llm_calls": [],
        "issues": [],
        "suggestions": [],
        "raw_llm_analysis": {},
        "error": None,
        "crop_size": None,
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
    existing_text = result.get("extracted_text", "")
    result["extracted_text"] = vision.get("visible_text", "") or existing_text
    result["category"] = metadata.get("category") or vision.get("probable_category") or "Uncategorized"
    result["tags"] = metadata.get("tags", [])
    result["seo_title"] = metadata.get("seo_title", "")
    result["product_name_suggestions"] = metadata.get("product_name_suggestions", [])

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

def _add_llm_usage(result: dict[str, Any], llm_meta: dict[str, Any]) -> None:
    cost = _parse_cost(llm_meta.get("estimated_cost", ""))
    if cost > 0:
        result["llm_cost"] = round(float(result.get("llm_cost", 0) or 0) + cost, 8)
        result["llm_cost_display"] = _format_cost(result["llm_cost"])
    result.setdefault("llm_calls", []).append(
        {
            "model_name": llm_meta.get("model_name", ""),
            "model_group": llm_meta.get("model_group", ""),
            "prompt_tokens": llm_meta.get("prompt_tokens", 0),
            "completion_tokens": llm_meta.get("completion_tokens", 0),
            "total_tokens": llm_meta.get("total_tokens", 0),
            "estimated_cost": llm_meta.get("estimated_cost", ""),
        }
    )


def _parse_cost(value: Any) -> float:
    return parse_cost(value)


def _format_cost(value: float) -> str:
    return format_cost(value)


def _emit_stage(
    job_id: str | None,
    stage_id: str,
    status: str,
    message: str = "",
    llm_meta: dict[str, Any] | None = None,
) -> None:
    label, default_model, default_type = LOCAL_STAGE_META[stage_id]
    start_percent, end_percent = STAGE_PERCENT[stage_id]
    percent = end_percent if status in {"completed", "skipped", "failed"} else start_percent
    llm_meta = llm_meta or {}
    model_name = llm_meta.get("model_name") or default_model
    progress_manager.emit(
        job_id,
        {
            "stage_id": stage_id,
            "stage": label,
            "status": status,
            "percent": percent,
            "message": message,
            "model_name": model_name,
            "model_type": model_type_for(model_name, default_type),
            "tokens_used": llm_meta.get("total_tokens", 0),
            "prompt_tokens": llm_meta.get("prompt_tokens", 0),
            "completion_tokens": llm_meta.get("completion_tokens", 0),
            "estimated_cost": llm_meta.get("estimated_cost", ""),
        },
    )
