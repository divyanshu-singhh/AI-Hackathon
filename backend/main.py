"""FastAPI entrypoint for the AI Product Image Quality, Tagging & Rebuilder backend."""

from pathlib import Path
from typing import Annotated
import asyncio
import uuid

import pandas as pd
import requests
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agents.orchestrator_agent import process_image
from config import DEFAULT_STAGES, MAX_BATCH_SIZE, REPORT_DIR, STORAGE_DIR, safe_runtime_config
from services.batch_processor import build_batch_response
from services.image_processor import download_image, normalize_image_url, save_upload_file
from services.progress_manager import progress_manager
from services.report_exporter import create_csv_report, report_path

app = FastAPI(title="AI Product Image Quality, Tagging & Rebuilder")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/storage", StaticFiles(directory=STORAGE_DIR), name="storage")


class SheetUrlRequest(BaseModel):
    csv_url: str
    stages: list[str] | None = None
    job_id: str | None = None
    crop_size: int | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-image-parser-agent"}


@app.get("/api/debug/config")
def debug_config() -> dict:
    """Safe setup diagnostics. Does not return secret values."""
    return safe_runtime_config()


@app.websocket("/ws/progress/{job_id}")
async def progress_websocket(websocket: WebSocket, job_id: str) -> None:
    await websocket.accept()
    queue = await progress_manager.subscribe(job_id)
    try:
        while True:
            event = await queue.get()
            await websocket.send_json(event)
    except WebSocketDisconnect:
        await progress_manager.unsubscribe(job_id, queue)


@app.post("/api/process-image")
async def process_single_image(
    image: Annotated[UploadFile, File()],
    stages: Annotated[str | None, Form()] = None,
    job_id: Annotated[str | None, Form()] = None,
    crop_size: Annotated[int | None, Form()] = None,
) -> dict:
    try:
        temp_path = await save_upload_file(image)
        return await asyncio.to_thread(
            process_image,
            temp_path,
            image.filename or temp_path.name,
            stages=parse_stages(stages),
            progress_job_id=job_id,
            crop_size=parse_crop_size(crop_size),
        )
    except Exception as exc:
        return {"status": "failed", "error": f"Unable to process image: {exc}"}


@app.post("/api/process-images")
async def process_multiple_images(
    images: Annotated[list[UploadFile], File()],
    stages: Annotated[str | None, Form()] = None,
    job_id: Annotated[str | None, Form()] = None,
    crop_size: Annotated[int | None, Form()] = None,
) -> dict:
    if len(images) > MAX_BATCH_SIZE:
        raise HTTPException(status_code=400, detail=f"Maximum batch size is {MAX_BATCH_SIZE}")
    paths = []
    for image in images:
        try:
            paths.append((await save_upload_file(image), image.filename or "upload.jpg", None))
        except Exception as exc:
            failed_path = Path(f"failed_{uuid.uuid4()}.jpg")
            paths.append((failed_path, image.filename or "upload.jpg", f"Upload failed: {exc}"))
    valid_paths = [(path, name, category) for path, name, category in paths if path.exists()]
    response = await asyncio.to_thread(build_batch_response, valid_paths, parse_stages(stages), job_id, parse_crop_size(crop_size))
    upload_failures = [
        {
            "image_id": str(uuid.uuid4()),
            "file_name": name,
            "status": "failed",
            "selected_stages": sorted(parse_stages(stages)),
            "error": category,
            "issues": [category] if category else [],
            "suggestions": [],
            "detected_objects": [],
            "tags": [],
        }
        for path, name, category in paths
        if not path.exists()
    ]
    if upload_failures:
        response["results"].extend(upload_failures)
        response["total"] += len(upload_failures)
        response["failed"] += len(upload_failures)
        report_name, report_url = create_csv_report(response["batch_id"], response["results"])
        response["report_name"] = report_name
        response["report_url"] = report_url
    return response


@app.post("/api/process-csv")
async def process_csv(
    csv_file: Annotated[UploadFile, File()],
    stages: Annotated[str | None, Form()] = None,
    job_id: Annotated[str | None, Form()] = None,
    crop_size: Annotated[int | None, Form()] = None,
) -> dict:
    try:
        temp_csv = await save_raw_upload(csv_file, ".csv")
        rows = pd.read_csv(temp_csv).fillna("").to_dict(orient="records")
        return await asyncio.to_thread(process_csv_rows, rows, parse_stages(stages), job_id, parse_crop_size(crop_size))
    except Exception as exc:
        return {"status": "failed", "error": f"Unable to process CSV: {exc}"}


@app.post("/api/process-sheet-url")
def process_sheet_url(payload: SheetUrlRequest) -> dict:
    try:
        response = requests.get(payload.csv_url, timeout=45)
        response.raise_for_status()
        temp_csv = REPORT_DIR / f"sheet_{uuid.uuid4()}.csv"
        temp_csv.write_bytes(response.content)
        rows = pd.read_csv(temp_csv).fillna("").to_dict(orient="records")
        return process_csv_rows(rows, set(payload.stages or DEFAULT_STAGES), payload.job_id, parse_crop_size(payload.crop_size))
    except Exception as exc:
        return {"status": "failed", "error": f"Unable to process sheet URL: {exc}"}


@app.get("/api/reports/{report_name}")
def download_report(report_name: str) -> FileResponse:
    path = report_path(report_name)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(path, media_type="text/csv", filename=path.name)


def parse_stages(raw: str | None) -> set[str]:
    if not raw:
        return set(DEFAULT_STAGES)
    requested = {item.strip() for item in raw.split(",") if item.strip()}
    allowed = set(DEFAULT_STAGES)
    selected = requested & allowed
    return selected or set(DEFAULT_STAGES)


def parse_crop_size(raw: int | None) -> int:
    return raw if raw in {125, 250, 500, 1000} else 1000


async def save_raw_upload(upload: UploadFile, expected_suffix: str) -> Path:
    suffix = Path(upload.filename or "").suffix.lower()
    if suffix != expected_suffix:
        raise ValueError(f"Expected a {expected_suffix} file")
    output_path = REPORT_DIR / f"upload_{uuid.uuid4()}{expected_suffix}"
    output_path.write_bytes(await upload.read())
    return output_path


def process_csv_rows(rows: list[dict], stages: set[str], job_id: str | None = None, crop_size: int = 1000) -> dict:
    if len(rows) > MAX_BATCH_SIZE:
        raise ValueError(f"Maximum batch size is {MAX_BATCH_SIZE}")

    paths = []
    failed_results = []
    for row in rows:
        image_url = _row_value(row, "image_url", "image url", "imageurl", "url", "image", "photo_url", "photo url", "product_image", "product image", allow_url_fallback=True)
        image_url = normalize_image_url(image_url)
        image_name = _row_value(row, "image_name", "image name", "filename", "file_name", "name") or Path(image_url).name or "downloaded_image.jpg"
        expected_category = _row_value(row, "expected_category", "expected category", "category") or None
        if not image_url:
            failed_results.append(_failed_csv_result(image_name, "Missing image_url", stages))
            continue
        try:
            paths.append((download_image(image_url, image_name), image_name, expected_category))
        except Exception as exc:
            failed_results.append(_failed_csv_result(image_name, f"Download failed: {exc}", stages))

    response = build_batch_response(paths, stages, job_id, crop_size) if paths else {
        "batch_id": str(uuid.uuid4()),
        "total": 0,
        "success": 0,
        "failed": 0,
        "results": [],
        "report_name": None,
        "report_url": None,
    }
    if failed_results:
        response["results"].extend(failed_results)
        response["total"] += len(failed_results)
        response["failed"] += len(failed_results)
    report_name, report_url = create_csv_report(response["batch_id"], response["results"])
    response["report_name"] = report_name
    response["report_url"] = report_url
    return response


def _failed_csv_result(file_name: str, error: str, stages: set[str]) -> dict:
    return {
        "image_id": str(uuid.uuid4()),
        "file_name": file_name,
        "status": "failed",
        "selected_stages": sorted(stages),
        "error": error,
        "issues": [error],
        "suggestions": [],
        "detected_objects": [],
        "tags": [],
    }


def _row_value(row: dict, *keys: str, allow_url_fallback: bool = False) -> str:
    """Read CSV values with common spelling/case variants."""
    normalized = {str(key).strip().lower(): value for key, value in row.items()}
    for key in keys:
        value = normalized.get(key.strip().lower())
        if value is not None and str(value).strip():
            return str(value).strip()

    # Last resort: accept any cell containing an http/image data URL.
    if allow_url_fallback:
        for value in row.values():
            text = str(value or "").strip()
            if "http://" in text or "https://" in text or text.startswith("data:image/"):
                return text
    return ""
