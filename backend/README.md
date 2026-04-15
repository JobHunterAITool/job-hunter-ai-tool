# The Job Hunting AI Web Tool - Backend

FastAPI backend foundation for CS467 Capstone Progress Report #1.

This backend provides:
- `POST /search` job ranking stub (frontend-ready contract)
- `GET /jobs` paginated jobs from MongoDB
- `POST /upload-resume` optional resume upload/preview stub
- Automatic seed of 10 fake jobs when DB collection is empty

## Tech Stack

- Python
- FastAPI
- Uvicorn
- PyMongo
- MongoDB (local)
- Optional parsing dependencies: `pdfplumber`, `python-docx`

## Project Structure

```text
backend/
  main.py
  db.py
  models/
    schemas.py
  routes/
    search.py
    jobs.py
    upload_resume.py
  services/
    ranking.py
    resume_parser.py
  seed/
    seed_jobs.py
  requirements.txt
  .env.example
```

## Prerequisites

- Python 3.10+ (recommended: Python 3.11+)
- Local MongoDB Community Server running on `mongodb://localhost:27017`
- Optional: `mongosh` to inspect data

## 1) Start MongoDB Locally

Use one of the following approaches.

### Option A: MongoDB Installed as a Service (Windows)

1. Check service status:
```powershell
Get-Service MongoDB
```
2. Start the service if needed:
```powershell
net start MongoDB
```

### Option B: Run `mongod` manually

1. Create a data directory once:
```powershell
mkdir C:\data\db
```
2. Start MongoDB:
```powershell
mongod --dbpath C:\data\db
```

If you are on macOS/Linux, start MongoDB with your package manager/service manager (for example `brew services start mongodb-community` or `sudo systemctl start mongod`).

## 2) Create and Activate a Virtual Environment

Run these commands from the project root:

```powershell
cd "c:\Users\micha\OneDrive\Desktop\OSU\Spring 2026\CS 467 Online Capstone Project\Project Folder"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

macOS/Linux equivalent:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3) Install Backend Dependencies

```powershell
pip install -r backend\requirements.txt
```

## 4) Configure Environment Variables

Copy the sample file:

```powershell
Copy-Item backend\.env.example backend\.env
```

Current environment variables:

- `MONGO_URI` default: `mongodb://localhost:27017`
- `MONGO_DB_NAME` default: `job_ai_tool`
- `JOBS_COLLECTION_NAME` default: `jobs`
- `CORS_ORIGINS` default: `http://localhost:3000,http://127.0.0.1:3000`

You can edit `backend/.env` if your local MongoDB uses a different URI or DB name.

## 5) Run the Backend

Run from project root:

```powershell
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Expected startup behavior:
- App boots successfully.
- Startup hook checks `job_ai_tool.jobs`.
- If empty, 10 seed jobs are inserted.

## 6) Verify It Is Running

Open:

- Swagger docs: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Health check: `http://127.0.0.1:8000/`

Health check response:

```json
{
  "status": "ok",
  "message": "Job Hunting AI Web Tool backend is running"
}
```

## API Endpoints

### `POST /search`

Request body:

```json
{
  "job_title": "Software Engineer",
  "skills": ["Python", "AWS"],
  "location": "Remote",
  "experience_level": "Mid"
}
```

Example response shape:

```json
{
  "results": [
    {
      "title": "Software Engineer",
      "company": "Amazon",
      "location": "Remote",
      "score": 0.99,
      "matched_skills": ["Python", "AWS"]
    }
  ]
}
```

Notes:
- Pulls all jobs from MongoDB.
- Calls `services/ranking.py -> rank_jobs_stub(...)`.
- Returns top 10 ranked results.
- Ranking logic is a placeholder and marked for future ML replacement.

### `GET /jobs?page=1&limit=20`

Query params:
- `page` default `1`, minimum `1`
- `limit` default `20`, range `1-100`

Example response shape:

```json
{
  "page": 1,
  "limit": 20,
  "total": 10,
  "results": [
    {
      "title": "Software Engineer",
      "company": "Amazon",
      "location": "Remote",
      "skills": ["Python", "AWS", "Docker"],
      "experience_level": "Mid"
    }
  ]
}
```

### `POST /upload-resume` (Optional)

Form-data field:
- `file` (PDF or DOCX recommended)

Behavior:
- Accepts upload.
- Uses optional parser helper to extract a short text preview.
- Returns placeholder message + preview when extraction succeeds.

PowerShell test:

```powershell
curl.exe -X POST "http://127.0.0.1:8000/upload-resume" `
  -F "file=@C:\path\to\resume.pdf"
```

## Quick Test Commands

### Search endpoint (PowerShell)

```powershell
$body = @{
  job_title = "Software Engineer"
  skills = @("Python", "AWS")
  location = "Remote"
  experience_level = "Mid"
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/search" `
  -ContentType "application/json" `
  -Body $body
```

### Jobs endpoint (PowerShell)

```powershell
Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8000/jobs?page=1&limit=5"
```

## Troubleshooting

### `ModuleNotFoundError: No module named 'fastapi'`

Cause:
- Dependencies not installed in the active environment.

Fix:
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

### `pymongo.errors.ServerSelectionTimeoutError`

Cause:
- MongoDB not running or URI mismatch.

Fix:
- Start MongoDB service/process.
- Verify `MONGO_URI` in `backend/.env`.
- Confirm port `27017` is open locally.

### `422 Unprocessable Entity` on `/search`

Cause:
- Request JSON missing required fields.

Fix:
- Ensure all fields are present: `job_title`, `skills`, `location`, `experience_level`.

### Upload endpoint fails on multipart error

Cause:
- Missing `python-multipart`.

Fix:
```powershell
pip install python-multipart
```

## Frontend Integration Notes

- CORS is enabled for:
  - `http://localhost:3000`
  - `http://127.0.0.1:3000`
- Update `CORS_ORIGINS` in `backend/.env` if frontend host/port changes.
- Response contracts are stable and intended for immediate frontend integration.

## Where ML Will Plug In Later

- Current ranking is stubbed in `backend/services/ranking.py`.
- Keep route call signature the same:
  - `rank_jobs_stub(search_input, jobs, top_n=10)`
- Replace only ranking internals with model inference later to avoid breaking API contract.
