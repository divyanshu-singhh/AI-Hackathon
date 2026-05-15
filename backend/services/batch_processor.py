"""Batch helpers shared by CSV and multi-file processing."""

import uuid
from pathlib import Path
from typing import Any

from agents.orchestrator_agent import process_image
from services.report_exporter import create_csv_report


def build_batch_response(
    paths: list[tuple[Path, str, str | None]],
    stages: set[str],
    progress_job_id: str | None = None,
    crop_size: int = 1000,
) -> dict[str, Any]:
    batch_id = str(uuid.uuid4())
    results = [
        process_image(
            path,
            file_name,
            expected_category=expected_category,
            stages=stages,
            progress_job_id=progress_job_id,
            crop_size=crop_size,
        )
        for path, file_name, expected_category in paths
    ]
    success = sum(1 for result in results if result.get("status") == "success")
    report_name, report_url = create_csv_report(batch_id, results)
    return {
        "batch_id": batch_id,
        "total": len(results),
        "success": success,
        "failed": len(results) - success,
        "report_name": report_name,
        "report_url": report_url,
        "results": results,
    }
