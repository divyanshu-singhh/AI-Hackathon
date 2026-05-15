# AI Product Image Quality, Tagging & Rebuilder

Hackathon MVP for product/catalog image parsing, quality auditing, background removal, clean image rebuilding, metadata generation, and CSV reporting.

The app has:

- FastAPI backend for image processing and reports.
- React + Vite frontend for uploads and results.
- Agent-style pipeline with selectable stages: quality, background removal, rebuild, vision analysis, and metadata generation. The frontend starts with local stages selected so LLM stages run only when you choose them.
- Internal OpenAI-compatible LLM gateway support through environment variables only.

## Project Structure

```text
backend/      FastAPI API, agents, services, schemas, local storage
frontend/     React + Vite dashboard
scripts/      Setup, run, cleanup, and sample curl helpers
references/   Gateway notes, prompts, schemas, demo script
assets/       Sample CSV and image folder notes
skill.md      Agent capability description
```

## Requirements

Install these first:

- Python 3.10+
- Node.js 18+
- npm

Optional:

- Tesseract is not required.
- `rembg` may download its model on first background-removal run, so the first request can be slower.

## Backend Setup

From the project root:

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment.

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Git Bash / Linux / macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create the backend environment file:

```bash
cp ../.env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item ..\.env.example .env
```

Edit `backend/.env`:

```env
IM_LLM_API_KEY=your_actual_access_key
VISION_MODEL=openai/gpt-4o
TEXT_MODEL=openai/gpt-4.1-mini
```

Never commit `.env`.

## Run Backend

From `backend/` with the virtual environment active:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok","service":"ai-image-parser-agent"}
```

## Frontend Setup

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:5173
```

## Scripted Setup

From the project root:

```bash
bash scripts/setup_backend.sh
bash scripts/setup_frontend.sh
bash scripts/run_backend.sh
bash scripts/run_frontend.sh
```

## How To Use

1. Start the backend at `http://localhost:8000`.
2. Start the frontend at `http://localhost:5173`.
3. Pick the processing stages you want to run. Vision and metadata are optional LLM stages.
4. Use one upload mode:
   - Single image
   - Multiple images
   - CSV file
   - Google Sheet CSV export URL
5. Review original, background-removed, rebuilt image, quality score, objects, tags, issues, and suggestions.
6. Download the generated CSV report for batch runs.

## CSV Format

Use this header:

```csv
image_name,image_url,expected_category,notes
```

Example:

```csv
sample_chair,https://example.com/chair.jpg,Furniture,Demo row only
```

## API Endpoints

- `GET /health`
- `POST /api/process-image`
- `POST /api/process-images`
- `POST /api/process-csv`
- `POST /api/process-sheet-url`
- `GET /api/reports/{report_name}`

For upload endpoints, pass selected stages as a comma-separated form field:

```text
stages=quality,background,rebuild,vision,metadata
```

## Notes For New Developers

- The main pipeline is in `backend/agents/orchestrator_agent.py`.
- LLM gateway calls are isolated in `backend/services/llm_client.py`.
- Deterministic OpenCV quality checks are in `backend/services/quality_analyzer.py`.
- Background removal has a fallback: if `rembg` fails, the app keeps processing.
- If the LLM key is missing or the gateway fails, the app returns fallback metadata instead of crashing.

## Known Limitations

- Batch processing is synchronous for the hackathon MVP.
- Very large batches should be moved to a queue/worker system later.
- OCR is handled through the vision model; local OCR is not mandatory in this version.
- CSV image URLs must be public and directly downloadable.
