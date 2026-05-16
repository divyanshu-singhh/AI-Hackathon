"""CSV/JSON report generation for batch results."""

import csv
import json
from pathlib import Path
from typing import Any

from config import REPORT_DIR, storage_url

REPORT_COLUMNS = [
    "image_name",
    "status",
    "main_product",
    "product_name_suggestions",
    "category",
    "detected_objects",
    "extracted_text",
    "tags",
    "quality_score",
    "rebuilt_quality_score",
    "issues",
    "suggestions",
    "original_image_url",
    "background_removed_image_url",
    "rebuilt_image_url",
    "error",
]


def create_csv_report(batch_id: str, results: list[dict[str, Any]]) -> tuple[str, str]:
    report_name = f"{batch_id}_report.csv"
    report_path = REPORT_DIR / report_name

    with report_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=REPORT_COLUMNS)
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "image_name": result.get("file_name", ""),
                    "status": result.get("status", ""),
                    "main_product": result.get("main_product", ""),
                    "product_name_suggestions": "; ".join(result.get("product_name_suggestions", [])),
                    "category": result.get("category", ""),
                    "detected_objects": "; ".join(result.get("detected_objects", [])),
                    "extracted_text": result.get("extracted_text", ""),
                    "tags": "; ".join(result.get("tags", [])),
                    "quality_score": result.get("quality_score", ""),
                    "rebuilt_quality_score": result.get("rebuilt_quality_score", ""),
                    "issues": "; ".join(result.get("issues", [])),
                    "suggestions": "; ".join(result.get("suggestions", [])),
                    "original_image_url": result.get("original_image_url", ""),
                    "background_removed_image_url": result.get("background_removed_image_url", ""),
                    "rebuilt_image_url": result.get("rebuilt_image_url", ""),
                    "error": result.get("error", ""),
                }
            )
    return report_name, storage_url("reports", report_name)


def create_json_report(batch_id: str, results: list[dict[str, Any]]) -> tuple[str, str]:
    report_name = f"{batch_id}_report.json"
    report_path = REPORT_DIR / report_name
    report_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return report_name, storage_url("reports", report_name)


def report_path(report_name: str) -> Path:
    return REPORT_DIR / Path(report_name).name
