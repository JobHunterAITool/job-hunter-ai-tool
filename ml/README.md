# ML Ranking Module

This module ranks job postings against a user's resume/profile text using a baseline TF‑IDF + cosine similarity approach.

## Public Interface (Contract)

### Function

```python
rank_jobs(user_profile: dict[str, Any], jobs: list[dict]) -> list[dict]
```

### Purpose

Given a user profile dictionary and a list of candidate jobs, return the jobs sorted by best match. This function is intended to be called by the Backend `POST /search` handler after it fetches a candidate set (e.g., top 200) from MongoDB.

### Input: `user_profile`

- Type: `dict[str, Any]`
- Description: User inputs provided by backend aggregation logic.
- Supported keys:
  - `user_text` (string): raw resume/profile text
  - `resume_text` (string): alternate key for extracted resume text
  - `job_title` (string): frontend job title field
  - `skills` (`list[str] | str`): list of skills or comma-separated skills
  - `location` (string): frontend location field
  - `experience_level` (string): frontend experience selector
- Edge cases:
  - If all supported keys are empty/absent, the function raises a ValueError

> **Note:** The module currently normalizes structured fields into a single text query before scoring. This keeps the API flexible while the ML implementation remains a stub.

### Input: `jobs`

- Type: `list[dict]`
- Each job is a Python `dict` (usually originating from MongoDB documents).
- Recommended/expected keys (missing keys are treated as empty strings):
  - `_id` (string): stable identifier (MongoDB)
  - `title` (string)
  - `company` (string)
  - `location` (string, optional)
  - `description` (string)
  - `category` (string): Could be used to break ties
  - `created` (string): Date when the job was posted
  - `redirect_url` (string): Used to webscrape `job_description_text`
  - `skills` (`list[str] | str`): Preferred shape is `list[str]`, but comma-separated `str` also accepted
  - `job_description_text` (string)

> **Missing fields:** If any of the above keys are missing, the ranking logic should treat the missing value as an empty string rather than raising an exception.

### Output

- Type: `list[dict]`
- The returned list must be **sorted descending** by match score (best match first).
- Each returned job dict must include:
  - `score`: `float` in `[0.0, 1.0]` (cosine similarity)

#### Non-destructive behavior (recommended)

The function should **not mutate** the input job dictionaries in-place. It should return **copies** with added `score` field to avoid unexpected side effects in the backend.

### Pagination / Top-N slicing responsibility

- The ML function returns **all** ranked jobs it receives.
- The backend is responsible for selecting top N (e.g., top 20) and implementing pagination/load-more behavior.

### Determinism and ties

If multiple jobs have equal scores, preserve the original order of the input list among tied items where practical.

### Error handling

Recommended behavior:

- In development: raise exceptions to make issues obvious.
- In production: if ranking fails unexpectedly, fall back to returning jobs in original order with `score = 0.0`.

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

- Text parsing of 'description' field for 'skills'
- Keyword pre-filtering before TF‑IDF scoring for latency
- Text normalization improvements
- Optional LogisticRegression

## Quick Start

### 1. Create & activate a virtual environment

#### Windows (PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
```

#### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
```

### 2. Install dependencies

```powershell
python -m pip install -r ml/requirements.txt
```

### 3. Run tests

#### 3.1. Run full test suite

```powershell
python -m pytest -vv
```

#### 3.2. Run full test suite with outputs

```powershell
python -m pytest -s -vv
```

#### 3.3. Run regular unit tests only with outputs

```powershell
python -m pytest tests/test_rank_jobs.py -s -v
```

#### 3.4. Run seed-data tests only with outputs

```powershell
python -m pytest tests/test_rank_jobs_seed.py -s -v
```
