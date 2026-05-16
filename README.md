# AI Product Image Quality, Tagging & Rebuilder

This project is a local Windows-friendly hackathon app for product image processing.

It has:

- Backend: Python FastAPI
- Frontend: React + Vite
- Features: image upload, quality score, background removal, final catalog image, optional AI product identification/title generation, CSV batch report
- Live processing timeline showing current stage, percentage, model/tool name, model type, LLM token usage, and gateway cost when available
- Output crop sizes: `125x125`, `250x250`, and `500x500`
- Optional OCR text detection stage
- Product name suggestions based on image analysis and visible text

## 1. Open PowerShell

Open PowerShell and go to the project folder:

```powershell
cd C:\Users\IndiaMart\Desktop\AI-Hackathon\ai-image-parser-agent
```

## 2. Backend Setup

Go to backend folder:

```powershell
cd backend
```

Create virtual environment only if `.venv` does not already exist:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install Python packages:

```powershell
python -m pip install -r requirements.txt
```

Create backend environment file:

```powershell
Copy-Item ..\.env.example .env
```

Open `backend\.env` in Notepad:

```powershell
notepad .env
```

Set your LLM key:

```env
IM_LLM_API_KEY=your_actual_access_key
VISION_MODEL=openai/gpt-4o
TEXT_MODEL=openai/gpt-4.1
FALLBACK_TEXT_MODEL=qwen/qwen3-32b
LLM_DEBUG=false
```

Save and close Notepad.

## 3. Run Backend

In the same backend PowerShell window, run:

```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Keep this PowerShell window open.

Check backend in browser:

```text
http://localhost:8000/health
```

Expected result:

```json
{"status":"ok","service":"ai-image-parser-agent"}
```

Check whether the backend can see your LLM key:

```text
http://localhost:8000/api/debug/config
```

Look for:

```json
"api_key_configured": true
```

If it is `false`, create or fix `backend\.env`, then restart backend.

## 4. Frontend Setup

Open a second PowerShell window.

Go to frontend folder:

```powershell
cd C:\Users\IndiaMart\Desktop\AI-Hackathon\ai-image-parser-agent\frontend
```

Install frontend packages:

```powershell
npm install
```

Run frontend:

```powershell
npm run dev
```

Keep this second PowerShell window open.

Open the app in browser:

```text
http://localhost:5173
```

## 5. How To Use The App

1. Open `http://localhost:5173`.
2. Select processing stages you want to run.
3. Start with these safe local stages:
   - Check Image Quality
   - Remove Background
   - Create Final Image
   Add `Read Text from Image`, `Identify Product`, and `Create Title & Tags` when the LLM key is configured.
4. Select output crop size: `125x125`, `250x250`, or `500x500`.
5. Select one or more product images.
6. Click `Process Image`.
7. Watch the `Processing Timeline` table for current stage, percentage, model/tool used, and LLM token usage.
8. Review original image, final image, quality score, issues, and suggestions.

Use `Identify Product` and `Create Title & Tags` only after `IM_LLM_API_KEY` is set in `backend\.env`.

## 6. Processing Stages

The app shows simple names in the UI, while the backend keeps short internal stage IDs such as `quality`, `background`, `rebuild`, `ocr`, `vision`, and `metadata`.

| UI stage name | Internal ID | What it does | Tool/API used |
|---|---|---|---|
| Check Image Quality | `quality` | Checks blur, brightness, contrast, noise, resolution, and background complexity. Produces the quality score, issues, and suggestions. | Local OpenCV |
| Remove Background | `background` | Removes the existing background and creates a product-focused image. | Local `rembg` / U2-Net |
| Create Final Image | `rebuild` | Crops the product tighter, enlarges it within the selected size, places it on a clean white canvas, and applies basic corrections. | Local Pillow/OpenCV |
| Read Text from Image | `ocr` | Reads visible text such as brand, label, model number, size, or printed product text. | Vision LLM API |
| Identify Product | `vision` | Looks at the image and identifies the main product, visible objects, category clues, colors, material, packaging, and other visual details. | Vision LLM API |
| Create Title & Tags | `metadata` | Converts the identified product details and quality result into catalog fields such as title, product name suggestions, category, tags, issues, and suggestions. | Text LLM API |

`Identify Product` and `Create Title & Tags` work together:

- `Identify Product` understands what is visible in the image.
- `Create Title & Tags` uses that understanding to create catalog-ready text.

## 7. CSV Image URL Input

CSV upload can fetch images from public URLs, then process them like uploaded files.

Recommended CSV columns:

```csv
image_name,image_url,expected_category,notes
tmt_bars,https://example.com/tmt-bars.jpg,Steel Bars,Demo image
```

Accepted image URL column names:

- `image_url`
- `Image URL`
- `imageUrl`
- `url`
- `photo_url`
- `product_image`

Google Sheet image formulas are also supported:

```csv
image_name,image_url
tmt_bars,"=IMAGE(""https://example.com/tmt-bars.jpg"")"
```

The URL must be reachable by the backend machine. If a site blocks downloads, the row will fail with a readable error in the batch report.

## 8. LLM Debug Logs

The project uses this endpoint:

```text
POST https://imllm.intermesh.net/v1/chat/completions
```

The backend reads the model output from:

```text
choices[0].message.content
```

If an LLM model fails or returns unexpected JSON, enable debug logs:

```powershell
cd C:\Users\IndiaMart\Desktop\AI-Hackathon\ai-image-parser-agent\backend
notepad .env
```

Change:

```env
LLM_DEBUG=true
```

Restart backend after changing `.env`.

The logs will show status code, model group, usage, response preview, and JSON parse errors. They do not print the API key or image base64.

## 9. Common Problems

### PowerShell blocks activation

If this command fails:

```powershell
.\.venv\Scripts\Activate.ps1
```

Run this once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then try activation again:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Port already in use

If port `8000` is busy, stop the old backend window or run:

```powershell
Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess
```

Then stop that process:

```powershell
Stop-Process -Id PROCESS_ID -Force
```

Replace `PROCESS_ID` with the number shown by the previous command.

### Virtual environment already exists

If `.venv` already exists, do not run `python -m venv .venv` again.

Just activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then install packages:

```powershell
python -m pip install -r requirements.txt
```

## 10. Useful Test Commands

Run backend test:

```powershell
cd C:\Users\IndiaMart\Desktop\AI-Hackathon\ai-image-parser-agent\backend
.\.venv\Scripts\Activate.ps1
pytest -q
```

Build frontend:

```powershell
cd C:\Users\IndiaMart\Desktop\AI-Hackathon\ai-image-parser-agent\frontend
npm run build
```

## 11. Important Files

- Backend main file: `backend\main.py`
- Backend environment file: `backend\.env`
- Frontend main UI: `frontend\src\App.jsx`
- API client: `frontend\src\api\client.js`
- Image pipeline: `backend\agents\orchestrator_agent.py`
- Sample CSV: `assets\sample_batch.csv`

## 12. Stop The App

To stop backend or frontend, go to each PowerShell window and press:

```text
Ctrl + C
```
