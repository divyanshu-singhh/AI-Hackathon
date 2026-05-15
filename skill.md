# Skill: AI Product Image Parser, Quality Auditor & Rebuilder

## Purpose

This skill processes product/catalog images and converts them into structured, catalog-ready outputs.

## Capabilities

1. Detect product/content from an image.
2. Extract visible text using vision LLM and OCR fallback.
3. Generate product category and tags.
4. Analyze image quality using deterministic CV metrics.
5. Remove background.
6. Rebuild image into a clean catalog-ready layout.
7. Generate improvement suggestions.
8. Export structured JSON/CSV reports.

## Inputs

- Single image upload.
- Multiple image upload.
- CSV batch file.
- Public Google Sheet CSV URL.

## Outputs

For each image:

- original_image_url
- background_removed_image_url
- rebuilt_image_url
- detected_objects
- extracted_text
- category
- tags
- quality_score
- quality_breakdown
- issues
- suggestions
- processing_status

## Internal Agents

### 1. Orchestrator Agent

Responsible for coordinating the full pipeline.

Steps:
1. Validate image.
2. Resize/compress safely.
3. Run only user-selected stages.
4. Run quality analyzer.
5. Run background remover.
6. Run vision analysis.
7. Run metadata generation.
8. Run image rebuilder.
9. Return final structured result.

### 2. Image Analysis Agent

Uses the vision model to understand image content.

Responsibilities:
- Detect main product.
- Detect secondary objects.
- Extract visible text.
- Identify category.
- Identify product attributes.

### 3. Quality Agent

Uses OpenCV metrics to calculate:
- Blur score.
- Brightness.
- Contrast.
- Noise estimate.
- Resolution check.
- Background complexity.

### 4. Metadata Agent

Uses text LLM to convert raw findings into:
- SEO title.
- Product category.
- Tags.
- Search keywords.
- Catalog improvement suggestions.

### 5. Rebuilder Agent

Uses image-processing libraries to:
- Place product on clean background.
- Center object.
- Add optional padding.
- Export PNG/WebP output.

## Accuracy Strategy

For hackathon demo, target controlled accuracy >= 85%.

Use:
- Vision LLM for semantic understanding.
- OpenCV for measurable quality.
- rembg for segmentation/background removal.
- Text LLM for structured metadata.

## Constraints

- Do not hardcode access keys.
- Do not use paid third-party APIs apart from provided internal LLM gateway.
- Keep all processed files local.
- Return valid JSON only from agent methods.
