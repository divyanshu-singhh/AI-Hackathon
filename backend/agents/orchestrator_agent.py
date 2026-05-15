"""Pipeline coordinator that runs only the frontend-selected processing stages."""

import uuid
from pathlib import Path
from typing import Any

from config import DEFAULT_STAGES, OUTPUT_DIR, TEXT_MODEL, VISION_MODEL, storage_url
from agents.image_analysis_agent import analyze_image, fallback_image_analysis
from agents.metadata_agent import fallback_metadata, generate_metadata
from agents.quality_agent import summarize_quality
from services.background_remover import remove_background
from services.image_processor import copy_to_uploads, normalize_image, resize_for_llm, validate_image_path
from services.image_rebuilder import rebuild_catalog_image
from services.progress_manager import model_type_for, progress_manager
from services.quality_analyzer import analyze_quality

LOCAL_STAGE_META = {
    "validate": ("Validate & Save", "Python/Pillow", "Open source local tool"),
    "quality": ("Quality Analysis", "OpenCV", "Open source local tool"),
    "background": ("Background Removal", "rembg U2-Net", "Open source local tool"),
    "rebuild": ("Image Rebuild", "Pillow", "Open source local tool"),
    "vision": ("Vision Analysis", VISION_MODEL, model_type_for(VISION_MODEL)),
    "metadata": ("Metadata Generation", TEXT_MODEL, model_type_for(TEXT_MODEL)),
    "finalize": ("Finalize Result", "FastAPI", "Open source local tool"),
}

STAGE_PERCENT = {
    "validate": (3, 12),
    "quality": (12, 28),
    "background": (28, 48),
    "rebuild": (48, 62),
    "vision": (62, 82),
    "metadata": (82, 94),
    "finalize": (94, 100),
}


def process_image(
    image_path: str | Path,
    original_filename: str,
    expected_category: str | None = None,
    stages: set[str] | None = None,
    progress_job_id: str | None = None,
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
            _emit_stage(progress_job_id, "rebuild", "running", message="Building 1000x1000 clean catalog image")
            rebuilt_output = OUTPUT_DIR / f"{image_id}_rebuilt.png"
            rebuild_catalog_image(bg_removed_path, rebuilt_output)
            result["rebuilt_image_url"] = storage_url("outputs", rebuilt_output.name)
            _emit_stage(progress_job_id, "rebuild", "completed", message="Catalog image rebuilt")
        else:
            _emit_stage(progress_job_id, "rebuild", "skipped", message="Skipped by user")

        vision = {}
        if "vision" in selected_stages:
            _emit_stage(progress_job_id, "vision", "running", message="Sending resized image to vision model")
            llm_image_path = resize_for_llm(uploaded_path, image_id)
            try:
                vision = analyze_image(llm_image_path)
                _emit_stage(
                    progress_job_id,
                    "vision",
                    "completed",
                    message="Vision model returned product analysis",
                    llm_meta=vision.get("_llm_meta", {}),
                )
            except Exception as exc:
                vision = fallback_image_analysis(original_filename, str(exc))
                result["issues"].append("LLM analysis failed; fallback result used.")
                _emit_stage(progress_job_id, "vision", "failed", message=str(exc))
        else:
            result["issues"].append("Vision stage skipped by user.")
            _emit_stage(progress_job_id, "vision", "skipped", message="Skipped by user")

        metadata = {}
        if "metadata" in selected_stages:
            _emit_stage(progress_job_id, "metadata", "running", message="Generating catalog title, tags, and suggestions")
            try:
                metadata = generate_metadata(vision, quality, quality_summary, expected_category)
                _emit_stage(
                    progress_job_id,
                    "metadata",
                    "completed",
                    message="Metadata generated",
                    llm_meta=metadata.get("_llm_meta", {}),
                )
            except Exception as exc:
                metadata = fallback_metadata(vision, quality, quality_summary, expected_category, str(exc))
                result["issues"].append("LLM metadata failed; fallback result used.")
                _emit_stage(progress_job_id, "metadata", "failed", message=str(exc))
        else:
            result["issues"].append("Metadata stage skipped by user.")
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
