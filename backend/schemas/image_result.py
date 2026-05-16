from typing import Any
from pydantic import BaseModel, Field


class ImageResult(BaseModel):
    image_id: str
    file_name: str
    status: str = "success"
    selected_stages: list[str] = Field(default_factory=list)
    original_image_url: str | None = None
    background_removed_image_url: str | None = None
    rebuilt_image_url: str | None = None
    detected_objects: list[str] = Field(default_factory=list)
    extracted_text: str = ""
    main_product: str = ""
    category: str = "Uncategorized"
    tags: list[str] = Field(default_factory=list)
    seo_title: str = ""
    quality_score: int | None = None
    quality_breakdown: dict[str, Any] = Field(default_factory=dict)
    rebuilt_quality_score: int | None = None
    rebuilt_quality_breakdown: dict[str, Any] = Field(default_factory=dict)
    issues: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    raw_llm_analysis: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
