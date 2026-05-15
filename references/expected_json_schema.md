# Expected JSON Schema

```json
{
  "image_id": "uuid",
  "file_name": "chair.jpg",
  "status": "success",
  "selected_stages": ["quality", "background", "rebuild", "vision", "metadata"],
  "original_image_url": "http://localhost:8000/storage/uploads/file.png",
  "background_removed_image_url": "http://localhost:8000/storage/outputs/file.png",
  "rebuilt_image_url": "http://localhost:8000/storage/outputs/file.png",
  "detected_objects": ["chair"],
  "extracted_text": "visible label text",
  "main_product": "wooden chair",
  "category": "Furniture",
  "tags": ["chair", "furniture"],
  "seo_title": "Wooden Chair",
  "quality_score": 86,
  "quality_breakdown": {
    "width": 1200,
    "height": 900,
    "blur_score": 124.4,
    "brightness": 142.1,
    "contrast": 58.2,
    "noise_score": 12.3,
    "resolution_ok": true
  },
  "issues": [],
  "suggestions": [],
  "raw_llm_analysis": {},
  "error": null
}
```
