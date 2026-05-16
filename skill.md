---
name: ai-image-parser-agent
description: Work on the AI Product Image Parser, Quality Auditor & Rebuilder project. Use when Codex needs to modify, debug, test, document, or extend the FastAPI/React app for product image upload, CSV/Sheet batch processing, image quality scoring, background removal, final catalog image creation, OCR, product identification, title/tag generation, report export, progress tracking, or LLM gateway cost tracking.
---

# AI Product Image Parser Agent

## Project Shape

Use this skill for the local hackathon app at `ai-image-parser-agent`.

- Backend: FastAPI in `backend/`
- Frontend: React + Vite in `frontend/`
- Image pipeline: `backend/agents/orchestrator_agent.py`
- Image utilities: `backend/services/`
- Frontend workflow shell: `frontend/src/App.jsx`
- User docs: `README.md`
- Detailed original requirements: `instructions.md`
- Reference prompts/schema: `references/`

Prefer reading the relevant local files before changing behavior. Keep edits small and aligned with existing patterns.

## Core Workflow

When changing product image processing behavior:

1. Trace the request through the UI component, API client, FastAPI endpoint, orchestrator, service, schema, CSV exporter, and tests as needed.
2. Preserve internal stage IDs unless the user explicitly asks for a breaking migration.
3. Keep user-facing labels non-technical.
4. Update result schemas, CSV exports, frontend tables/cards, and README together when adding result fields.
5. Run backend tests and frontend build before finishing.

## Stage Contract

Keep these internal IDs stable because requests, stored results, selected stages, progress events, and tests depend on them.

| Internal ID | User-facing label | Purpose | Tool/API |
|---|---|---|---|
| `quality` | Check Image Quality | Score blur, brightness, contrast, noise, resolution, and background complexity. Produce issues and suggestions. | Local OpenCV |
| `background` | Remove Background | Remove the image background and produce a product-focused cutout. | Local `rembg` / U2-Net |
| `rebuild` | Create Final Image | Crop, enlarge, center, correct, and place product on a clean catalog canvas. | Local Pillow/OpenCV |
| `ocr` | Read Text from Image | Read visible labels, brand text, model numbers, sizes, and printed text. | Vision LLM API |
| `vision` | Identify Product | Understand the image: main product, objects, probable category, color, material, packaging, visual details. | Vision LLM API |
| `metadata` | Create Title & Tags | Convert product understanding and quality data into catalog fields: title, product names, category, tags, issues, suggestions. | Text LLM API |

`vision` and `metadata` are different:

- `vision` reads the image and identifies what is visible.
- `metadata` uses that understanding to write catalog-ready text.

## Backend Guidance

Important backend files:

- `backend/main.py`: FastAPI endpoints.
- `backend/agents/orchestrator_agent.py`: stage order, progress events, result merging, LLM cost collection.
- `backend/agents/image_analysis_agent.py`: OCR and product identification prompts.
- `backend/agents/metadata_agent.py`: title/tag/catalog prompt.
- `backend/services/quality_analyzer.py`: original and final image quality scoring.
- `backend/services/image_rebuilder.py`: final image creation.
- `backend/services/report_exporter.py`: CSV/JSON report fields.
- `backend/schemas/`: response models.

Rules:

- Do not hardcode access keys or secrets.
- Read LLM gateway config from environment variables in `backend/config.py`.
- Preserve local processing for quality, background removal, and final image creation.
- Treat `x-litellm-response-cost` as an estimated USD cost unless the gateway contract changes.
- When adding a result field, update base result, schema, CSV exporter, frontend rendering, and tests where relevant.
- Failed CSV/download/upload rows should still produce readable report rows.

## Frontend Guidance

Important frontend files:

- `frontend/src/App.jsx`: upload mode, progress, result layout.
- `frontend/src/components/StageSelector.jsx`: visible stage labels only; keep internal stage keys.
- `frontend/src/components/BatchUploadPanel.jsx`: one or many image upload.
- `frontend/src/components/GoogleSheetPanel.jsx`: CSV/Sheet input.
- `frontend/src/components/ProgressTimeline.jsx`: live stage progress and cost.
- `frontend/src/components/BatchPreviewGrid.jsx`: image comparison cards.
- `frontend/src/components/ResultsTable.jsx`: batch/single table and CSV download.
- `frontend/src/styles/app.css`: shared styling.

Rules:

- Keep visible UI language simple for non-technical users.
- Prefer labels such as `Identify Product` over `Vision`, and `Create Title & Tags` over `Metadata`.
- Keep the `Image` tab able to process one or many images.
- Do not expose internal IDs in visible UI unless useful for debugging docs.
- Maintain responsive layout and avoid overlapping text/popovers.

## Image Quality And Final Image

The final image should be meaningfully better than a plain background-removed image.

When touching rebuild behavior:

- Avoid overexposing products because the original background is dark.
- Measure correction from product/subject pixels where possible.
- Crop transparent or white padding tightly.
- Enlarge the product within the selected canvas size without excessive blank space.
- Preserve product detail; sharpening and denoising should be conservative.
- Recalculate `rebuilt_quality_score` after creating the final image.

## LLM And Cost Handling

LLM calls go through the OpenAI-compatible internal gateway:

- Base URL/env: `IM_LLM_BASE_URL`
- API key/env: `IM_LLM_API_KEY`
- Vision model/env: `VISION_MODEL`
- Text model/env: `TEXT_MODEL`
- Fallback text model/env: `FALLBACK_TEXT_MODEL`

Each LLM response may include usage and `x-litellm-response-cost`.

When changing LLM behavior:

- Keep prompts strict JSON when downstream code parses JSON.
- Preserve `_llm_meta` handling through agents and orchestrator.
- Add per-image costs to result rows and sum them at batch level.
- Show costs as estimated USD unless verified otherwise.

## Documentation Updates

Update `README.md` when changing:

- stage names or meanings
- setup or run commands
- CSV input/output columns
- API behavior
- result table fields
- LLM cost behavior

Keep README user-facing and non-technical where possible.

## Validation

Use these commands from the project root unless context says otherwise.

Backend tests:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
```

Frontend build:

```powershell
cd frontend
npm run build
```

If a command cannot run because dependencies are missing, report that clearly and use the project virtual environment when available.
