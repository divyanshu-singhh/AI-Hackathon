# AI Product Image Quality, Tagging & Rebuilder

This project is a local Windows-friendly hackathon app for product image processing.

It has:

- Backend: Python FastAPI
- Frontend: React + Vite
- Features: image upload, quality score, background removal, rebuilt image, optional LLM-based vision/metadata, CSV batch report
- Live processing timeline showing current stage, percentage, model/tool name, model type, LLM token usage, and gateway cost when available

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
2. Select stages you want to run.
3. Start with these safe local stages:
   - Quality
   - Remove BG
   - Rebuild
4. Select one product image.
5. Click `Process Image`.
6. Watch the `Processing Timeline` table for current stage, percentage, model/tool used, and LLM token usage.
7. Review original image, rebuilt image, quality score, issues, and suggestions.

Use `Vision` and `Metadata` stages only after `IM_LLM_API_KEY` is set in `backend\.env`.

## 6. LLM Debug Logs

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

## 7. Common Problems

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

## 8. Useful Test Commands

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

## 9. Important Files

- Backend main file: `backend\main.py`
- Backend environment file: `backend\.env`
- Frontend main UI: `frontend\src\App.jsx`
- API client: `frontend\src\api\client.js`
- Image pipeline: `backend\agents\orchestrator_agent.py`
- Sample CSV: `assets\sample_batch.csv`

## 10. Stop The App

To stop backend or frontend, go to each PowerShell window and press:

```text
Ctrl + C
```
