from pydantic import BaseModel, Field
from schemas.image_result import ImageResult


class BatchResult(BaseModel):
    batch_id: str
    total: int
    success: int
    failed: int
    report_url: str | None = None
    report_name: str | None = None
    results: list[ImageResult] = Field(default_factory=list)
