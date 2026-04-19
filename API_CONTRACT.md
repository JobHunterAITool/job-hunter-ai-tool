# API Contract

**Project:** The Job Hunting AI Web Tool  
**Frontend:** React + Vite  
**Backend:** FastAPI (single deployable app, modular monolith)  
**Data Format:** JSON  
**Base URL (local development):** http://localhost:8000

**Milestone 1 Input Mode:**
- Primary: send plain text profile input (typed or pasted resume text) to `POST /search`.
- Stretch goal: use `POST /upload-resume` for PDF/DOCX parsing.

---

## Contract Scope

- This document defines the external frontend-to-backend API contract.
- Internal module boundaries (`ranking`, `resume_parser`, DB helpers) are implementation details inside the same FastAPI app.
- No separate ML microservice API is part of the public contract in this phase.

## Non-Goals (Current Phase)

- No inter-service HTTP/gRPC contracts.
- No message queue or event bus contract.
- No independent ML deployment contract.

---

## API Endpoints

| Method | Endpoint | Purpose |
|------|------|------|
| POST | /upload-resume | Upload and preview a resume (stretch goal for Milestone 1) |
| POST | /search | Search and rank job results |
| GET | /jobs | Retrieve paginated job listings |
| GET | /health | Confirm backend availability |

---

## 1. POST /upload-resume (Stretch Goal)

### Purpose
Accept a resume file uploaded from the frontend.

Note: This endpoint is optional for Milestone 1 and does not block core search functionality.

### Request
Content-Type: `multipart/form-data`

| Field | Type | Description |
|------|------|-------------|
| file | file | Resume file (`.pdf` or `.docx`) |

### Success Response (200)

```json
{
  "filename": "resume.pdf",
  "message": "Resume uploaded successfully",
  "text": "Software developer with Python and React experience...",
  "extracted_text_preview": "Software developer with Python and React experience..."
}
```

### Response Fields

| Field | Type | Description |
|------|------|-------------|
| filename | string | Original uploaded filename |
| message | string | Status message |
| text | string or null | Text preview used by the frontend |
| extracted_text_preview | string or null | Backward-compatible alias during transition |

### Errors

- `400` invalid file type
- `413` file too large
- `422` validation/parsing failure
- `500` unexpected server error

---

## 2. POST /search

### Purpose
Accept structured search input and return ranked job results.

### Request
Content-Type: `application/json`

```json
{
  "profile_text": "Python developer with FastAPI and React experience...",
  "job_title": "Software Engineer",
  "skills": ["Python", "React"],
  "location": "Remote",
  "experience_level": "Mid"
}
```

`profile_text` is required for Milestone 1 and accepts multiline freeform text.

### Request Fields

| Field | Type | Description |
|------|------|-------------|
| profile_text | string | Required freeform profile text (typed or pasted resume text) |
| job_title | string | Optional desired role title |
| skills | string[] | Optional list of user skills |
| location | string | Optional preferred job location |
| experience_level | string | Optional desired experience level |

### Success Response (200)

```json
{
  "results": [
    {
      "id": "job_10234",
      "title": "Software Engineer",
      "company": "Amazon",
      "location": "Remote",
      "score": 0.99,
      "matched_skills": ["Python"]
    }
  ]
}
```

### Job Result Object

| Field | Type | Description |
|------|------|-------------|
| id | string | Stable job identifier |
| title | string | Job title |
| company | string | Company name |
| location | string | Job location |
| score | number | Relevance score in `[0,1]` |
| matched_skills | string[] | Overlap between input skills and job skills |

### Error Responses

- `400` invalid request body
- `422` validation error
- `500` unexpected server error

### Notes (Stub Phase)

- Ranking is currently module-based and may use placeholder scoring while ML evolves.
- Request shape and response shape should remain stable for frontend integration.

---

## 3. GET /jobs

### Purpose
Return paginated job postings from MongoDB.

### Query Parameters

| Parameter | Type | Description |
|----------|------|-------------|
| page | integer | Page number (default: `1`) |
| limit | integer | Jobs per page (default: `20`) |

### Success Response (200)

```json
{
  "page": 1,
  "limit": 10,
  "total": 10,
  "results": [
    {
      "id": "job_10234",
      "title": "Software Engineer",
      "company": "Amazon",
      "location": "Remote",
      "skills": ["Python", "AWS", "Docker"],
      "experience_level": "Mid"
    }
  ]
}
```

### Response Fields

| Field | Type | Description |
|------|------|-------------|
| page | number | Current page |
| limit | number | Number of jobs returned per page |
| total | number | Total number of jobs available |
| results | array | Job documents for the requested page |

### Job Object

| Field | Type | Description |
|------|------|-------------|
| id | string | Unique job identifier |
| title | string | Job title |
| company | string | Company name |
| location | string | Job location |
| skills | string[] | Skills associated with the posting |
| experience_level | string | Experience level for the role |

### Error Responses

- `400` invalid query parameters
- `500` unexpected server error

---

## 4. GET /health

### Purpose
Provide a lightweight availability check.

### Success Response (200)

```json
{
  "status": "ok"
}
```

### Compatibility Note

`GET /` may also return a health payload during active development for backward compatibility, but `GET /health` is the canonical contract endpoint.

---

## Standard Error Response Format

```json
{
  "error": "Error type",
  "detail": "Explanation"
}
```

---

## Shared Validation Rules

Milestone 1 profile input:

- `profile_text` is required on `POST /search`.
- `profile_text` may contain multiline pasted resume text.

Accepted resume file types (stretch goal upload path):

- `.pdf`
- `.docx`

Recommended upload limit:

- 5 MB maximum file size

---

## Backend Responsibilities (Contract Stability)

- Keep endpoint paths and payload shapes stable across module refactors.
- Return JSON-only responses.
- Provide clear validation errors.

## Frontend Responsibilities

- Show loading and error states.
- Collect freeform profile text before calling `POST /search`.
- Validate file type before uploading resumes (stretch goal path).
- Handle null `text` / preview values safely.
- Treat `id` as stable result identity.

---

## Team Agreement

To prevent frontend/backend integration issues:

1. Endpoint names remain stable:
  - `POST /upload-resume` (stretch goal)
  - `POST /search`
  - `GET /jobs`
  - `GET /health`
2. Request and response field names remain stable unless the team agrees to changes.
3. Backend changes affecting request or response structures must be communicated before implementation.
4. Frontend integration must follow this contract document.
