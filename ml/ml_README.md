# ML Ranking Module

This module ranks job postings against a user's resume/profile text using a baseline TF‑IDF + cosine similarity approach.

## Quick Start

### 1) Create & activate a virtual environment

**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
```

**Windows (PowerShell)**
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
```

### 2) Install dependencies

```bash
python -m pip install -r ml/requirements.txt
```

### 3) Run tests

```bash
python -m pytest
```

## Public Interface (Contract)

### Function

```python
rank_jobs(user_text: str, jobs: list[dict]) -> list[dict]
```

### Purpose

Given resume/profile text and a list of candidate jobs, return the jobs sorted by best match. This function is intended to be called by the Backend `POST /search` handler after it fetches a candidate set (e.g., top 200) from MongoDB.

### Input: `user_text`

- Type: `str`
- Description: Raw extracted resume text (or fallback manual input text) provided by the backend.
- Edge cases:
  - If `user_text` is empty or whitespace-only, the function should not crash. Recommended behavior is to return all jobs with scores set to `0.0`.

### Input: `jobs`

- Type: `list[dict]`
- Each job is a Python `dict` (usually originating from MongoDB documents).
- Recommended/expected keys (missing keys are treated as empty strings):
  - `id` (string): stable identifier (preferred if available)
  - `title` (string)
  - `company` (string)
  - `location` (string, optional)
  - `description` (string)
  - `skills` (optional): either `list[str]` or a comma-separated `str`

> **Missing fields:** If any of the above keys are missing, the ranking logic should treat the missing value as an empty string rather than raising an exception.

### Output

- Type: `list[dict]`
- The returned list must be **sorted descending** by match score (best match first).
- Each returned job dict must include:
  - `match_score`: `float` in `[0.0, 1.0]` (cosine similarity)
  - `match_percent`: `int` in `[0, 100]` (rounded from `match_score * 100`)

#### Non-destructive behavior (recommended)

The function should **not mutate** the input job dictionaries in-place. It should return **copies** with added `match_score` / `match_percent` fields to avoid unexpected side effects in the backend.

### Pagination / Top-N slicing responsibility

- The ML function returns **all** ranked jobs it receives.
- The backend is responsible for selecting top N (e.g., top 20) and implementing pagination/load-more behavior.

### Determinism and ties

If multiple jobs have equal scores, preserve the original order of the input list among tied items where practical.

### Error handling

Recommended behavior:
- In development: raise exceptions to make issues obvious.
- In production: if ranking fails unexpectedly, fall back to returning jobs in original order with `match_score = 0.0` and `match_percent = 0`.

## Seed Data

This repo includes seed job data for development/testing:

- `./seed_jobs.json`

## Implementation Notes (Baseline)

Baseline algorithm target:
- Build a TF‑IDF representation of:
  - the user text, and
  - each job’s combined text fields (e.g., title + description + skills)
- Compute cosine similarity between user vector and each job vector
- Attach scores and sort

Future improvements (planned):
- Keyword pre-filtering before TF‑IDF scoring for latency
- Text normalization improvements
- Optional embedding-based ranking upgrade (sentence-transformers)