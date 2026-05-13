# ML Ranking Module

This module ranks job postings against a user's resume/profile text using a
baseline TF-IDF cosine similarity score blended with explicit skill matching.
The blended final scores are L2-normalized before being returned to the
backend.

## Public Interface (Contract)

### Function

```python
rank_jobs(
    user_profile: dict[str, Any],
    jobs: list[dict[str, Any]],
    debug: bool = True,
    debug_top_n: int = 5,
) -> list[dict[str, Any]]
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
  - `experience_level` (int): years of experience
- Edge cases:
  - If all supported keys are empty/absent, the function raises a ValueError

> **Note:** `experience_level` is expected to be an integer number of years.
> The ranker still tolerates legacy string values for direct callers and maps
> common labels such as `entry`, `junior`, `mid`, `senior`, and `lead` to
> approximate year values.

### Input: `jobs`

- Type: `list[dict]`
- Each job is a Python `dict` (usually originating from MongoDB documents).
- Recommended/expected keys (missing keys are treated as empty strings):
  - `_id` (string): stable identifier (MongoDB)
  - `title` (string)
  - `company` (string)
  - `location` (string, optional)
  - `description` (string): short/truncated description from the source API
  - `category` (string): Could be used to break ties
  - `created` (string): Date when the job was posted
  - `redirect_url` (string): Used to webscrape `job_description_text`
  - `skills` (`list[str] | str`): Preferred shape is `list[str]`, but comma-separated `str` also accepted
  - `job_description_text` (string): full scraped/plain-text job description used in TF-IDF text

> **Missing fields:** If any of the above keys are missing, the ranking logic should treat the missing value as an empty string rather than raising an exception.

### Output

- Type: `list[dict]`
- The returned list must be **sorted descending** by match score (best match first).
- Each returned job dict must include:
  - `score`: `float` in `[0.0, 1.0]`, the final L2-normalized blended score returned to the backend
  - `matched_skills`: `list[str]`, sorted intersection of user skills and job skills
  - `matched_skills_count`: `int`
  - `tfidf_score`: `float`, raw cosine similarity before blending
  - `skill_score`: `float`, fraction of user skills matched by the job
  - `raw_final_score`: `float`, blended score before final L2 normalization

#### Non-destructive behavior

The function does **not mutate** the input job dictionaries in-place. It returns
shallow copies with scoring and match fields added.

### Pagination / Top-N slicing responsibility

- The ML function returns **all** ranked jobs it receives.
- The backend is responsible for selecting top N (e.g., top 20) and implementing pagination/load-more behavior.

### Determinism and ties

If multiple jobs have equal scores, preserve the original order of the input list among tied items where practical.

### Debug Output

By default, `rank_jobs(..., debug=True)` prints the normalized query terms and
the top ranked jobs. The per-job debug output only prints the final normalized
`score` returned to the backend, plus matched skill/term context. Intermediate
scores remain attached to returned job dictionaries for inspection.

### Error handling

Recommended behavior:

- In development: raise exceptions to make issues obvious.
- In production: if ranking fails unexpectedly, fall back to returning jobs in original order with `score = 0.0`.

## Seed Data

This repo includes seed job data for development/testing:

- `./seed_jobs.json`
- `./pipeline/pulled_jobs_from_mongodb.json`

## Implementation Notes (Baseline)

Current algorithm:

- Normalize user inputs into one query string:
  - `user_text` or `resume_text`
  - `job_title`
  - `skills`
  - `location`
  - integer `experience_level` as years of experience
- Preprocess text with spaCy lemmatization and stop-word/punctuation removal.
- For large candidate sets, prefilter to the top 200 jobs by keyword overlap
  while preserving input order as a tie-breaker.
- Build TF-IDF text from each job's title, full `job_description_text`, and
  skills.
- Compute cosine similarity between the user vector and each candidate job.
- Compute a skill score from exact normalized skill intersections.
- Blend scores with `alpha = 0.4`:
  - `raw_final_score = 0.6 * tfidf_score + 0.4 * skill_score`
- Apply L2 normalization to the complete `raw_final_score` vector.
- Store the normalized value as `score` and sort descending.

Future improvements (planned):

- Text parsing of 'description' field for 'skills'
- Text normalization improvements
- Better final-score display scaling, such as min-max normalization for more
  user-friendly match percentages
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

#### 3.5. Run MongoDB fixture ranking tests only

```powershell
python -m pytest tests/test_rank_jobs_mongodb.py tests/test_backend_ranking_mongodb_integration.py -s -v
```
