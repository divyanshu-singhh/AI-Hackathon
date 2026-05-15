# AI Product Image Parser, Quality Auditor & Rebuilder — Codex/Claude Build Instructions

## 0. Project Goal

Build a full-stack agentic web application for the hackathon problem:

> Intelligent Image Parser — cost-effective image content detector, background remover, text fetcher, data tagger, and image rebuilder with at least 80% practical accuracy for controlled product/catalog images.

The app should allow users to:

1. Upload a single product image.
2. Select and upload multiple images from the system.
3. Upload a CSV file similar to a Google Sheet export containing image URLs.
4. Optionally provide a public Google Sheet CSV export URL for batch processing.
5. Process each image using:
   - Vision-capable LLM for image understanding, OCR, object/category detection.
   - OpenCV for image quality analysis.
   - rembg/U²-Net for background removal.
   - Pillow/OpenCV for image rebuilding.
   - Text LLM for final product metadata generation.
6. Show results in the UI:
   - Original image.
   - Background removed image.
   - Rebuilt clean image.
   - Extracted text.
   - Detected objects.
   - Product category.
   - Generated product tags.
   - Quality score.
   - Issues.
   - Improvement suggestions.
7. Export results as CSV/JSON report.

Important: Use the company internal LLM gateway. Do not hardcode tokens.

---

## 1. Recommended Tech Stack

### Frontend

Use:

```bash
React + Vite
```

Reason:
- Fast to build.
- Easy upload UI.
- Easy result cards/grid/table.
- Good demo experience.

### Backend

Use:

```bash
Python FastAPI
```

Reason:
- Best ecosystem for image processing.
- Easy support for OpenCV, Pillow, rembg, Tesseract/EasyOCR.
- Simple REST APIs for frontend.

### Image Processing

Use:

```bash
opencv-python
Pillow
rembg
numpy
```

Optional OCR fallback:

```bash
pytesseract
```

### LLM Gateway

Use OpenAI-compatible REST API.

Internal LLM base URL:

```text
https://imllm.intermesh.net
```

Endpoint:

```text
POST /v1/chat/completions
```

Required header:

```text
Authorization: Bearer <your-access-key>
Content-Type: application/json
```

Do not store the access key in code. Use environment variables.

---

## 2. Model Strategy

Use model names from environment variables so we can switch easily.

Recommended defaults:

```env
VISION_MODEL=openai/gpt-4o
TEXT_MODEL=openai/gpt-4.1-mini
FALLBACK_TEXT_MODEL=openrouter/qwen/qwen3-32b
```

Alternative vision models allowed from available list:

```text
qwen/qwen2.5-vl-32b-instruct
qwen/qwen2.5-vl-72b-instruct
meta-llama/llama-3.2-90b-vision-instruct
openrouter/meta-llama/llama-3.2-90b-vision-instruct
openai/gpt-4o
openai/gpt-4o-mini
```

If a model rejects image input, fallback to:
1. OCR via local OCR if available.
2. OpenCV quality checks.
3. Send extracted text + quality JSON to text LLM.

---

## 3. Accuracy Expectation

For selected hackathon demo images:

| Capability | Practical Expected Accuracy |
|---|---:|
| Object/content detection | 85–95% |
| OCR on clean images | 80–95% |
| Product category/tagging | 85–95% |
| Background removal | 85–95% |
| Blur/brightness/noise scoring | 75–90% |
| Rebuilt image quality | 75–85% |

Target controlled accuracy:

```text
>= 80%
```

Important:
- Resize large images before processing.
- Use clean catalog/product images for demo.
- Avoid heavily occluded, handwritten, or extremely noisy images during demo.

---

## 4. Final Application Name

Use this name in UI:

```text
AI Product Image Quality, Tagging & Rebuilder
```

Tagline:

```text
Upload product images and generate catalog-ready images, metadata, quality scores, and improvement suggestions.
```

---

## 5. Required Repository Structure

Create this project structure:

```text
ai-image-parser-agent/
│
├── instructions.md
├── README.md
├── .env.example
├── .gitignore
│
├── skill.md
│
├── scripts/
│   ├── setup_backend.sh
│   ├── setup_frontend.sh
│   ├── run_backend.sh
│   ├── run_frontend.sh
│   ├── run_all.sh
│   ├── clean_outputs.sh
│   └── sample_curl.sh
│
├── references/
│   ├── llm_gateway.md
│   ├── prompt_templates.md
│   ├── expected_json_schema.md
│   ├── csv_input_format.md
│   └── demo_script.md
│
├── assets/
│   ├── sample_images/
│   │   └── README.md
│   ├── sample_batch.csv
│   └── ui_wireframe.md
│
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── services/
│   │   ├── llm_client.py
│   │   ├── image_processor.py
│   │   ├── quality_analyzer.py
│   │   ├── background_remover.py
│   │   ├── image_rebuilder.py
│   │   ├── batch_processor.py
│   │   └── report_exporter.py
│   ├── agents/
│   │   ├── image_analysis_agent.py
│   │   ├── metadata_agent.py
│   │   ├── quality_agent.py
│   │   └── orchestrator_agent.py
│   ├── schemas/
│   │   ├── image_result.py
│   │   └── batch_result.py
│   ├── storage/
│   │   ├── uploads/
│   │   ├── outputs/
│   │   ├── reports/
│   │   └── temp/
│   └── tests/
│       └── test_health.py
│
└── frontend/
    ├── package.json
    ├── index.html
    ├── vite.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── api/
        │   └── client.js
        ├── components/
        │   ├── Header.jsx
        │   ├── UploadPanel.jsx
        │   ├── BatchUploadPanel.jsx
        │   ├── GoogleSheetPanel.jsx
        │   ├── ResultCard.jsx
        │   ├── ResultsTable.jsx
        │   ├── QualityScore.jsx
        │   ├── ImageCompare.jsx
        │   └── Loader.jsx
        └── styles/
            └── app.css
```

---

## 6. Agent-Focused Files and Folders

This section is important. Build the project as an agentic solution, not just a basic upload app.

### 6.1 `skill.md`

Create a root-level `skill.md` that explains what this agent does, how it thinks, what tools it uses, and what output format it guarantees.

`skill.md` should contain:

```markdown
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
3. Run quality analyzer.
4. Run background remover.
5. Run vision analysis.
6. Run metadata generation.
7. Run image rebuilder.
8. Return final structured result.

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
```

### 6.2 `scripts/`

Use this folder for repeatable setup and demo commands.

Required scripts:

#### `scripts/setup_backend.sh`

Should:
- Create Python venv.
- Install requirements.
- Create storage folders.

#### `scripts/setup_frontend.sh`

Should:
- Run `npm install`.

#### `scripts/run_backend.sh`

Should:
- Start FastAPI backend at port 8000.

#### `scripts/run_frontend.sh`

Should:
- Start Vite frontend at port 5173.

#### `scripts/run_all.sh`

Should:
- Print instructions to run backend and frontend.
- If possible, start both in separate background processes.

#### `scripts/clean_outputs.sh`

Should:
- Clear `backend/storage/uploads`.
- Clear `backend/storage/outputs`.
- Clear `backend/storage/reports`.
- Keep `.gitkeep` files.

#### `scripts/sample_curl.sh`

Should contain a working curl:

```bash
curl -X POST "http://localhost:8000/api/process-image" \
  -F "image=@assets/sample_images/sample.jpg"
```

### 6.3 `references/`

Use this folder as the knowledge base for the implementation and demo.

Create these files:

#### `references/llm_gateway.md`

Include internal LLM details:

```markdown
# Internal LLM Gateway

Base URL:

https://imllm.intermesh.net

Endpoint:

POST /v1/chat/completions

Headers:

Authorization: Bearer <access-key>
Content-Type: application/json

Environment variables:

IM_LLM_BASE_URL=https://imllm.intermesh.net
IM_LLM_API_KEY=your_key_here
VISION_MODEL=openai/gpt-4o
TEXT_MODEL=openai/gpt-4.1-mini

Never hardcode access keys.
```

#### `references/prompt_templates.md`

Include system and user prompts for:
- Vision analysis.
- Metadata generation.
- Final quality summary.

#### `references/expected_json_schema.md`

Document the final output JSON.

#### `references/csv_input_format.md`

Document batch input format:

```csv
image_name,image_url,expected_category,notes
sample1.jpg,https://example.com/sample1.jpg,Furniture,Wooden chair
sample2.jpg,https://example.com/sample2.jpg,Industrial Pump,Contains label text
```

#### `references/demo_script.md`

Add the demo talk track:

```markdown
1. Upload product image.
2. Show original image.
3. Show detected product and text.
4. Show background removed image.
5. Show quality score and issues.
6. Show generated title/tags/category.
7. Show rebuilt catalog-ready image.
8. Export batch report.
```

### 6.4 `assets/`

Use this folder for local demo assets.

Required:

```text
assets/sample_images/
assets/sample_batch.csv
assets/ui_wireframe.md
```

Do not commit heavy images. Add only small demo images or a README explaining where to place images.

---

## 7. Environment File

Create `.env.example`:

```env
# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
MAX_IMAGE_SIZE_MB=10
MAX_BATCH_SIZE=50

# Internal LLM Gateway
IM_LLM_BASE_URL=https://imllm.intermesh.net
IM_LLM_API_KEY=replace_with_your_access_key

# Models
VISION_MODEL=openai/gpt-4o
TEXT_MODEL=openai/gpt-4.1-mini
FALLBACK_TEXT_MODEL=openrouter/qwen/qwen3-32b

# Output
PUBLIC_BACKEND_URL=http://localhost:8000
OUTPUT_IMAGE_FORMAT=png
```

Create `.gitignore`:

```gitignore
.env
__pycache__/
*.pyc
.venv/
node_modules/
dist/
backend/storage/uploads/*
backend/storage/outputs/*
backend/storage/reports/*
backend/storage/temp/*
!backend/storage/uploads/.gitkeep
!backend/storage/outputs/.gitkeep
!backend/storage/reports/.gitkeep
!backend/storage/temp/.gitkeep
.DS_Store
```

---

## 8. Backend Requirements

Create `backend/requirements.txt`:

```txt
fastapi
uvicorn[standard]
python-multipart
python-dotenv
requests
pydantic
opencv-python
pillow
numpy
rembg
onnxruntime
pandas
```

Optional if adding local OCR fallback:

```txt
pytesseract
```

Do not make Tesseract mandatory because it also requires OS-level installation.

---

## 9. Backend API Design

Create FastAPI app with these endpoints:

### 9.1 Health Check

```text
GET /health
```

Response:

```json
{
  "status": "ok",
  "service": "ai-image-parser-agent"
}
```

### 9.2 Single Image Processing

```text
POST /api/process-image
```

Input:

```text
multipart/form-data
image: file
```

Response:

```json
{
  "image_id": "uuid",
  "file_name": "chair.jpg",
  "status": "success",
  "original_image_url": "http://localhost:8000/storage/uploads/chair.jpg",
  "background_removed_image_url": "http://localhost:8000/storage/outputs/chair_bg_removed.png",
  "rebuilt_image_url": "http://localhost:8000/storage/outputs/chair_rebuilt.png",
  "detected_objects": ["chair", "wooden furniture"],
  "extracted_text": "Modern Wooden Chair",
  "category": "Furniture",
  "tags": ["wooden chair", "furniture", "home decor"],
  "seo_title": "Modern Wooden Chair for Home and Office",
  "quality_score": 86,
  "quality_breakdown": {
    "blur_score": 124.4,
    "brightness": 142.1,
    "contrast": 58.2,
    "noise_score": 12.3,
    "resolution_ok": true
  },
  "issues": ["Slightly low contrast"],
  "suggestions": ["Increase contrast slightly", "Use a plain white background"],
  "raw_llm_analysis": {},
  "error": null
}
```

### 9.3 Multi Image Processing

```text
POST /api/process-images
```

Input:

```text
multipart/form-data
images: multiple files
```

Response:

```json
{
  "batch_id": "uuid",
  "total": 3,
  "success": 3,
  "failed": 0,
  "results": []
}
```

### 9.4 CSV Batch Processing

```text
POST /api/process-csv
```

Input:

```text
multipart/form-data
csv_file: file
```

CSV columns:

```csv
image_name,image_url,expected_category,notes
```

Behavior:
- If `image_url` is present, download the image.
- Process each downloaded image.
- Include expected category in comparison if present.
- Generate report.

### 9.5 Google Sheet CSV URL Processing

```text
POST /api/process-sheet-url
```

Input JSON:

```json
{
  "csv_url": "https://docs.google.com/spreadsheets/d/.../export?format=csv"
}
```

Behavior:
- Download CSV.
- Process same as `/api/process-csv`.

### 9.6 Report Download

```text
GET /api/reports/{report_name}
```

Return generated CSV report.

### 9.7 Static Files

Mount storage folders:

```text
/storage/uploads
/storage/outputs
/storage/reports
```

---

## 10. Backend Implementation Details

### 10.1 `backend/config.py`

Responsibilities:
- Load env variables.
- Define paths.
- Ensure storage directories exist.

Expected variables:
- `IM_LLM_BASE_URL`
- `IM_LLM_API_KEY`
- `VISION_MODEL`
- `TEXT_MODEL`
- `MAX_IMAGE_SIZE_MB`
- `PUBLIC_BACKEND_URL`

### 10.2 `backend/services/llm_client.py`

Implement an OpenAI-compatible client using `requests`.

Functions:

```python
chat_completion(model: str, messages: list, temperature=0.2, max_tokens=1200) -> dict
```

For vision image input, use OpenAI-style message content:

```python
[
  {
    "role": "user",
    "content": [
      {
        "type": "text",
        "text": "Analyze this product image and return strict JSON..."
      },
      {
        "type": "image_url",
        "image_url": {
          "url": "data:image/jpeg;base64,<base64>"
        }
      }
    ]
  }
]
```

Important:
- Handle gateway errors gracefully.
- Log status code and response text for debugging.
- Do not expose access key in logs.
- Parse JSON safely.
- If the model returns markdown fenced JSON, strip code fences.

### 10.3 `backend/services/quality_analyzer.py`

Use OpenCV.

Compute:
- Width, height.
- Blur score using Laplacian variance.
- Brightness using grayscale mean.
- Contrast using grayscale standard deviation.
- Noise estimate using difference/variance.
- Resolution check.
- Aspect ratio.
- Basic background complexity estimate.

Return:

```python
{
  "width": 1200,
  "height": 900,
  "blur_score": 135.2,
  "brightness": 148.0,
  "contrast": 62.5,
  "noise_score": 10.2,
  "resolution_ok": true,
  "issues": [],
  "quality_score": 86
}
```

Suggested scoring:
- Start from 100.
- Deduct for:
  - Blur score < 80.
  - Brightness < 80 or > 220.
  - Contrast < 35.
  - Low resolution.
  - High noise.
- Clamp between 0 and 100.

### 10.4 `backend/services/background_remover.py`

Use `rembg`.

Function:

```python
remove_background(input_path: str, output_path: str) -> str
```

Return output path.

Handle failure:
- If rembg fails, copy original image to output and mark warning.

### 10.5 `backend/services/image_rebuilder.py`

Use Pillow.

Function:

```python
rebuild_catalog_image(bg_removed_path: str, output_path: str) -> str
```

Expected behavior:
- Create 1000x1000 white canvas.
- Open background-removed PNG with alpha.
- Resize product to fit within 800x800 while preserving aspect ratio.
- Center product.
- Add padding.
- Save as PNG.

### 10.6 `backend/agents/image_analysis_agent.py`

Uses vision model.

Prompt must ask for strict JSON:

```json
{
  "main_product": "",
  "detected_objects": [],
  "visible_text": "",
  "probable_category": "",
  "attributes": {
    "color": [],
    "material": [],
    "shape": "",
    "brand_or_label": ""
  },
  "confidence": 0.0
}
```

Prompt:

```text
You are an expert product image parser for an ecommerce/catalog platform.

Analyze the uploaded image.

Return ONLY valid JSON with:
- main_product
- detected_objects
- visible_text
- probable_category
- attributes
- confidence

Do not include markdown.
Do not include explanation outside JSON.
```

### 10.7 `backend/agents/metadata_agent.py`

Input:
- Vision JSON.
- Quality JSON.
- Optional expected category.

Output:

```json
{
  "seo_title": "",
  "category": "",
  "tags": [],
  "search_keywords": [],
  "issues": [],
  "suggestions": [],
  "catalog_readiness_score": 0
}
```

Prompt:

```text
You are a catalog metadata expert.

Given image analysis JSON and quality analysis JSON, generate product metadata.

Return ONLY valid JSON.

Rules:
- Keep title short and searchable.
- Tags should be practical for product discovery.
- Suggestions should be actionable.
- Do not invent brand name unless visible in text.
```

### 10.8 `backend/agents/quality_agent.py`

This agent converts deterministic quality metrics into a human-friendly explanation.

Input:
- OpenCV quality JSON.

Output:
- Quality label: Excellent/Good/Average/Poor.
- Issues.
- Suggestions.

This can be done with simple Python logic first. LLM optional.

### 10.9 `backend/agents/orchestrator_agent.py`

This is the main pipeline.

Function:

```python
process_image(image_path: str, original_filename: str) -> dict
```

Steps:

1. Generate `image_id`.
2. Validate file type.
3. Resize image if very large.
4. Save original.
5. Run quality analyzer.
6. Run background remover.
7. Run image rebuilder.
8. Run vision analysis.
9. Run metadata agent.
10. Merge all results.
11. Return final JSON.

Important:
- Every failure should be captured per image.
- Batch should continue even if one image fails.
- Return `status: failed` for failed image instead of crashing full batch.

---

## 11. Frontend UI Requirements

### 11.1 Main Screen Layout

Create clean dashboard UI:

```text
Header
  - App name
  - Tagline

Tabs or sections:
  1. Single Image
  2. Multi Image
  3. CSV / Google Sheet

Left side:
  - Upload panel
  - Process button

Right side:
  - Result preview
  - Quality score
  - Tags/category
  - Suggestions
```

### 11.2 Single Upload

Component:

```text
UploadPanel.jsx
```

Features:
- Drag and drop image.
- File picker.
- Preview selected image.
- Process button.
- Loading state.
- Error state.

### 11.3 Multi Upload

Component:

```text
BatchUploadPanel.jsx
```

Features:
- Select multiple images.
- Show list of selected image names.
- Process all.
- Show progress count.
- Show result grid/table.

### 11.4 Google Sheet / CSV

Component:

```text
GoogleSheetPanel.jsx
```

Features:
- CSV file upload.
- Text input for Google Sheet CSV export URL.
- Process button.
- Show batch report.
- Download CSV report button.

### 11.5 Result Card

Component:

```text
ResultCard.jsx
```

Show:
- Original image.
- Background removed image.
- Rebuilt image.
- Category.
- Tags as badges.
- OCR text.
- Quality score.
- Issues.
- Suggestions.

### 11.6 Results Table

Component:

```text
ResultsTable.jsx
```

Columns:
- Image name.
- Status.
- Category.
- Quality score.
- Objects.
- Tags.
- Issues.
- Download/View result.

### 11.7 Styling

Keep simple, professional, and demo-friendly.

Use CSS only. Avoid heavy UI libraries.

Suggested design:
- White/gray background.
- Cards with soft shadow.
- Green score for good quality.
- Yellow for average.
- Red for poor.
- Blue action buttons.

---

## 12. Frontend API Client

Create `frontend/src/api/client.js`.

Functions:

```javascript
export async function processSingleImage(file) {}
export async function processMultipleImages(files) {}
export async function processCsv(file) {}
export async function processSheetUrl(csvUrl) {}
```

Backend base URL:

```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
```

Create `frontend/.env.example`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## 13. CSV / Google Sheet Flow

### 13.1 CSV Input Format

Support this:

```csv
image_name,image_url,expected_category,notes
chair1,https://example.com/chair.jpg,Furniture,Wooden chair image
pump1,https://example.com/pump.jpg,Industrial Pump,Label visible
```

### 13.2 Google Sheet Flow

User should:
1. Create Google Sheet with same columns.
2. Publish as CSV or get export URL.
3. Paste URL in UI.
4. Backend downloads CSV.
5. Backend processes image URLs.
6. App shows batch results.
7. App allows CSV report download.

### 13.3 Report Output Columns

Generate report with:

```csv
image_name,
status,
main_product,
category,
detected_objects,
extracted_text,
tags,
quality_score,
issues,
suggestions,
original_image_url,
background_removed_image_url,
rebuilt_image_url,
error
```

---

## 14. Commands to Build Project

### 14.1 Create Project Folder

```bash
mkdir ai-image-parser-agent
cd ai-image-parser-agent
```

### 14.2 Ask Codex/Claude to Build

Give Codex/Claude this command/prompt:

```text
Read instructions.md fully and build the complete project exactly as specified.

Important:
- Create the full frontend and backend.
- Use FastAPI backend.
- Use React + Vite frontend.
- Implement the agentic folder structure.
- Create skill.md, scripts/, references/, and assets/.
- Use the internal OpenAI-compatible LLM gateway from environment variables.
- Do not hardcode API keys.
- Support single image upload, multiple image upload, CSV batch upload, and Google Sheet CSV URL batch processing.
- Use rembg for background removal, OpenCV for quality metrics, Pillow for rebuilt image, and the configured vision/text LLMs for image analysis and metadata generation.
- Make sure the app runs locally with clear setup scripts.
- Generate clean, working, production-readable code with error handling.
```

### 14.3 Backend Setup

From root:

```bash
cd backend
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Linux/Mac/Git Bash:

```bash
source .venv/bin/activate
```

Install:

```bash
pip install -r requirements.txt
```

Create `.env` from `.env.example`:

```bash
cp ../.env.example .env
```

On Windows PowerShell, if `cp` does not work:

```powershell
Copy-Item ..\.env.example .env
```

Edit `.env`:

```env
IM_LLM_API_KEY=your_actual_key
VISION_MODEL=openai/gpt-4o
TEXT_MODEL=openai/gpt-4.1-mini
```

Run backend:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 14.4 Frontend Setup

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

### 14.5 Full Run Through Scripts

Codex should create scripts so user can run:

```bash
bash scripts/setup_backend.sh
bash scripts/setup_frontend.sh
bash scripts/run_backend.sh
bash scripts/run_frontend.sh
```

---

## 15. Sample Backend Code Requirements

Codex must implement, not just stub.

### 15.1 `llm_client.py`

Must:
- Read env variables.
- Support text calls.
- Support image base64 calls.
- Return parsed JSON.
- Strip markdown fences.
- Handle errors.

### 15.2 Image Base64 Helper

Create helper:

```python
def image_to_data_url(path: str) -> str:
    # Determine MIME type
    # Read file bytes
    # Convert to base64
    # Return data:image/jpeg;base64,...
```

### 15.3 JSON Parser Helper

Create helper:

```python
def safe_parse_json(text: str) -> dict:
    # Remove ```json fences
    # Extract first JSON object if extra text exists
    # json.loads
    # Return dict or fallback error dict
```

---

## 16. Image Processing Rules

### 16.1 Resize Rule

Before sending image to LLM:
- Max dimension: 1024 px.
- Save compressed copy in temp folder.
- Do not send original 5–10 MB file directly.

### 16.2 File Validation

Allowed:
- jpg
- jpeg
- png
- webp

Reject:
- pdf
- exe
- zip
- svg for initial version

### 16.3 Output Naming

Use:

```text
{image_id}_original.jpg
{image_id}_bg_removed.png
{image_id}_rebuilt.png
```

### 16.4 Storage URLs

Return browser-accessible URLs:

```text
http://localhost:8000/storage/uploads/{file}
http://localhost:8000/storage/outputs/{file}
```

---

## 17. Prompts

### 17.1 Vision Analysis Prompt

```text
You are an expert product image parser for an ecommerce/catalog platform.

Analyze the uploaded product image.

Return ONLY valid JSON in this exact structure:

{
  "main_product": "",
  "detected_objects": [],
  "visible_text": "",
  "probable_category": "",
  "attributes": {
    "color": [],
    "material": [],
    "shape": "",
    "brand_or_label": "",
    "packaging": ""
  },
  "image_observations": [],
  "confidence": 0.0
}

Rules:
- Do not include markdown.
- Do not include explanation outside JSON.
- If text is not visible, use empty string.
- Do not invent brand names.
- detected_objects should include only visible objects.
- confidence should be from 0 to 1.
```

### 17.2 Metadata Prompt

```text
You are a product catalog metadata expert.

Given:
1. Vision analysis JSON
2. OpenCV quality analysis JSON
3. Optional expected category

Generate clean catalog metadata.

Return ONLY valid JSON in this exact structure:

{
  "seo_title": "",
  "category": "",
  "tags": [],
  "search_keywords": [],
  "quality_label": "",
  "issues": [],
  "suggestions": [],
  "catalog_readiness_score": 0
}

Rules:
- Do not invent unavailable brand names.
- Keep SEO title short, useful, and searchable.
- Tags should be lowercase and practical.
- Suggestions should be actionable.
- catalog_readiness_score should be 0 to 100.
- If OCR text conflicts with object detection, mention it in issues.
```

### 17.3 Batch Summary Prompt

Optional:

```text
You are analyzing a batch of product image processing results.

Generate a concise batch summary:
- total images
- success count
- failed count
- average quality score
- most common issues
- recommended next actions

Return ONLY valid JSON.
```

---

## 18. Local Demo Data

Create `assets/sample_batch.csv`:

```csv
image_name,image_url,expected_category,notes
sample_chair,https://example.com/chair.jpg,Furniture,Demo row only - replace URL
sample_pump,https://example.com/pump.jpg,Industrial Pump,Demo row only - replace URL
```

Create `assets/sample_images/README.md`:

```markdown
Place sample product images here for local testing.

Recommended demo image types:
- chair
- industrial pump
- packaged food product
- machine part with label
- apparel product

Keep images below 2 MB for faster demo.
```

---

## 19. Error Handling Requirements

Every API must return readable error.

For single image failure:

```json
{
  "status": "failed",
  "error": "Unable to process image: reason"
}
```

For batch:
- Continue processing other images.
- Mark failed image as failed.
- Do not crash whole batch.

LLM failure:
- Return CV results.
- Set metadata as fallback.
- Add issue: "LLM analysis failed; fallback result used."

Background removal failure:
- Continue with original image.
- Add issue: "Background removal failed."

---

## 20. Demo Flow

Use this exact demo sequence:

1. Open React app.
2. Upload one product image.
3. Click Process Image.
4. Show:
   - Original image.
   - Detected product.
   - Extracted text.
   - Background removed image.
   - Rebuilt catalog image.
   - Quality score.
   - Suggestions.
5. Go to Multi Image tab.
6. Select 3–5 images.
7. Process all.
8. Show result table.
9. Export CSV.
10. Open CSV report.

Demo pitch:

```text
This solution converts unstructured seller product images into catalog-ready assets. It detects content, extracts visible text, removes background, audits quality, rebuilds the image, and generates searchable tags and metadata. This can reduce manual catalog operations and improve listing quality.
```

---

## 21. Hackathon Judging Points

Make sure UI clearly shows:

### Business Value

```text
Reduces manual image checking and tagging effort.
Improves product catalog quality.
Helps sellers upload better images.
Can increase buyer trust and discovery.
```

### Technical Value

```text
Agentic pipeline using vision model + deterministic CV + image processing.
Fallback handling.
Batch processing.
Report generation.
```

### Scalability Story

```text
Currently local for hackathon.
Can be moved to queue-based architecture:
Frontend → API → Queue → Worker Pods → Object Storage → Report DB.
```

---

## 22. Future Architecture Slide Content

Add to `references/demo_script.md`:

```text
Production-ready architecture:

User Upload
  → Frontend
  → API Gateway
  → Image Processing Queue
  → Worker Pods
  → Object Storage/CDN
  → Metadata DB
  → Review Dashboard
  → Catalog System

Scale:
- Use async workers for heavy image processing.
- Store outputs in object storage.
- Cache repeated LLM results.
- Route large batches to background jobs.
```

---

## 23. Important Constraints

Codex must follow:

1. Do not hardcode API keys.
2. Do not commit `.env`.
3. Do not use paid third-party APIs except internal LLM gateway.
4. Keep code simple and readable.
5. Avoid unnecessary dependencies.
6. Make the demo run locally.
7. Handle image and LLM errors gracefully.
8. Use strict JSON from LLM.
9. Use deterministic OpenCV scoring for quality.
10. Return both image outputs and metadata.

---

## 24. Final Acceptance Criteria

Project is complete only if all below work:

### Backend

- `GET /health` works.
- `POST /api/process-image` works.
- `POST /api/process-images` works.
- `POST /api/process-csv` works.
- `POST /api/process-sheet-url` works.
- Static image URLs are viewable in browser.
- CSV report is generated.

### Frontend

- Single image upload works.
- Multiple image upload works.
- CSV upload works.
- Google Sheet CSV URL input exists.
- Results are displayed clearly.
- Report download works.
- Loading/error states work.

### Agentic Files

- `skill.md` exists.
- `scripts/` exists with all scripts.
- `references/` exists with gateway/prompt/schema/demo docs.
- `assets/` exists with sample CSV and sample image README.

---

## 25. One-Shot Prompt for Codex/Claude

Paste this into Codex/Claude after placing this `instructions.md` in the project root:

```text
You are building a hackathon MVP named "AI Product Image Quality, Tagging & Rebuilder".

Read the full instructions.md file in the root folder and implement the complete application.

Build:
1. FastAPI backend in /backend
2. React + Vite frontend in /frontend
3. Agentic documentation and folder structure:
   - skill.md
   - scripts/
   - references/
   - assets/

Important implementation requirements:
- Internal LLM gateway is OpenAI-compatible:
  Base URL: https://imllm.intermesh.net
  Endpoint: /v1/chat/completions
  Auth: Authorization Bearer token from IM_LLM_API_KEY env variable
- Do not hardcode the access key.
- Use VISION_MODEL and TEXT_MODEL env variables.
- Support image input to the vision model using base64 data URL in OpenAI-compatible message content.
- Use OpenCV for image quality checks.
- Use rembg for background removal.
- Use Pillow for rebuilding image on a clean white canvas.
- Support:
  a. single image upload
  b. multiple image upload
  c. CSV upload
  d. Google Sheet public CSV URL
- Generate CSV report.
- Add strong error handling.
- Keep code clean and runnable locally.

After implementation, provide:
1. Setup commands.
2. Run commands.
3. Any missing dependency notes.
4. Known limitations.
```

---

## 26. Extra: Minimal Terminal Commands for the Developer

After Codex builds the project:

```bash
cd ai-image-parser-agent
cp .env.example backend/.env
```

Edit `backend/.env` and set:

```env
IM_LLM_API_KEY=your_actual_key
VISION_MODEL=openai/gpt-4o
TEXT_MODEL=openai/gpt-4.1-mini
```

Run backend:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Windows PowerShell:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Run frontend:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

---

## 27. Notes for Windows Laptop

Your laptop is enough for this demo.

Use:
- Small images.
- Resize before LLM.
- Keep batch size 5–10 for live demo.
- Pre-install dependencies before demo.
- Run first background removal once before demo because rembg may download model on first run.

If rembg first run is slow, run this before demo:

```bash
python -c "from rembg import remove; print('rembg ready')"
```

---

## 28. Nice-to-Have Additions

Only add these after core flow works:

1. Progress bar for batch processing.
2. Side-by-side image comparison slider.
3. Quality score color gauge.
4. Batch summary using LLM.
5. Export JSON.
6. Retry failed images.
7. Model selector dropdown.
8. Manual correction of tags/category.
9. Before/after download button.
10. Accuracy comparison if expected category is provided in CSV.

---

## 29. Do Not Overbuild

Avoid these in hackathon MVP:

- Login/authentication.
- Database.
- Cloud storage.
- Kubernetes.
- Complex queue system.
- Real-time streaming.
- Large model local inference.
- Custom model training.

Build the working demo first.

IMPORTANT: there are multiple stages in our project. Do not run all the stages by default. RUn only those stages which we choose at front-end at the time of files upload.
