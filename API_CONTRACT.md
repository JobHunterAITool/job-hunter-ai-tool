# API Contract
**Project:** The Job Hunting AI Web Tool  
**Frontend:** React + Vite  
**Backend:** FastAPI  
**Data Format:** JSON  
**Base URL (local development):** http://localhost:8000

---

# API Endpoints

| Method | Endpoint | Purpose |
|------|------|------|
| POST | /upload-resume | Upload and preview a resume |
| POST | /search | Search and rank job results |
| GET | /jobs | Retrieve paginated job listings |
| GET | /health | Confirm backend availability |

---

# 1. POST /upload-resume

## Purpose
Accept a resume file uploaded from the frontend.

---

## Request

Content-Type:

multipart/form-data

Form field:

| Field | Type | Description |
|------|------|-------------|
| file | file | Resume file (.pdf or .docx) |

---

## Example Request

```javascript
const formData = new FormData();
formData.append("file", selectedFile);

await axios.post("/upload-resume", formData);
```

---

## Success Response

Status: 200 OK

```json
{
  "filename": "resume.pdf",
  "message": "Resume uploaded successfully",
  "text": "Software developer with Python and React experience..."
}
```

---

## Response Fields

| Field | Type | Description |
|------|------|-------------|
| filename | string | Original uploaded file name |
| message | string | Status message returned by the server |
| text | string or null | Short preview of extracted text |

---

## Error Responses

### Invalid File Type
Status: 400 Bad Request

```json
{
  "error": "Invalid file type",
  "detail": "Only PDF or DOCX files are supported"
}
```

### File Too Large
Status: 413 Payload Too Large

```json
{
  "error": "File too large",
  "detail": "Maximum upload size is 5 MB"
}
```

### Validation Error
Status: 422 Unprocessable Entity

```json
{
  "error": "Validation error",
  "detail": "The uploaded file could not be processed"
}
```

### Server Error
Status: 500 Internal Server Error

```json
{
  "error": "Server error",
  "detail": "An unexpected= error occurred while uploading the resume"
}
```

---

## Notes

Supported file types:

.pdf  
.docx  

If parsing fails or no text is found, "text" will be null.  

If the uploaded file exceeds the allowed size limit, the backend should return:

413 Payload Too Large

---

# 2. POST /search

## Purpose
Accept structured search input from the frontend and return ranked job results.

The backend retrieves job postings from MongoDB and applies a ranking service to compute relevance scores.  

---

## Request

Content-Type:

application/json

### Request Body

```json
{
  "job_title": "Software Engineer",
  "skills": ["Python", "React"],
  "location": "Remote",
  "experience_level": "Mid"
}
```

---

## Request Fields

| Field | Type | Description |
|------|------|-------------|
| job_title | string | Desired role title |
| skills | string[] | List of user skills |
| location | string | Preferred job location |
| experience_level | string | Desired experience level |

---

## Success Response

Status: 200 OK

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
    },
    {
      "id": "job_10235",
      "title": "Full Stack Engineer",
      "company": "Airbnb",
      "location": "San Francisco, CA",
      "score": 0.94,
      "matched_skills": ["Python", "React"]
    }
  ]
}
```

---

## Response Fields

| Field | Type | Description |
|------|------|-------------|
| results | array | Ranked job search results |

---

## Job Result Object

| Field | Type | Description |
|------|------|-------------|
| id | string | Unique job identifier |
| title | string | Job title |
| company | string | Company name |
| location | string | Job location |
| score | number | Relevance score between 0 and 1 |
| matched_skills | string[] | Skills shared between user input and job listing |

---

## Error Responses

### Invalid Request Body
Status: 400 Bad Request

```json
{
  "error": "Invalid request",
  "detail": "One or more request fields are missing or invalid"
}
```

### Validation Error
Status: 422 Unprocessable Entity

```json
{
  "error": "Validation error",
  "detail": "Request body does not match the required schema"
}
```

### Server Error
Status: 500 Internal Server Error

```json
{
  "error": "Server error",
  "detail": "An unexpected error occurred while processing the search request"
}
```

---

# 3. GET /jobs

## Purpose
Return a list of job postings stored in MongoDB.

---

## Request

Method:

GET

Query Parameters:

| Parameter | Type | Description |
|----------|------|-------------|
| page | integer | Page number (default: 1) |
| limit | integer | Number of jobs per page (default: 20) |

---

## Example Request

GET /jobs?page=1&limit=10

---

## Success Response

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

---

## Response Fields

| Field | Type | Description |
|------|------|-------------|
| page | number | Current page |
| limit | number | Number of jobs returned per page |
| total | number | Total number of jobs available |
| results | array | Job documents for the requested page |

---

## Job Object

| Field | Type | Description |
|------|------|-------------|
| id | string | Unique job identifier |
| title | string | Job title |
| company | string | Company name |
| location | string | Job location |
| skills | string[] | Skills associated with the posting |
| experience_level | string | Experience level for the role |

---

## Error Responses

### Invalid Query Parameters
Status: 400 Bad Request

```json
{
  "error": "Invalid query parameters",
  "detail": "Page and limit must be positive integers"
}
```

### Server Error
Status: 500 Internal Server Error

```json
{
  "error": "Server error",
  "detail": "An unexpected error occurred while retrieving jobs"
}
```

---

# 4. GET /health

## Purpose
Provide a simple endpoint the frontend or developers can use to confirm that the backend service is running.

---

## Success Response

Status: 200 OK

```json
{
  "status": "ok"
}
```

---

## Response Fields

| Field | Type | Description |
|------|------|-------------|
| status | string | Backend health status |

---

# Standard Error Response Format

All API errors should follow this structure:

```json
{
  "error": "Error type",
  "detail": "Explanation"
}
```

---

# Shared Validation Rules

Accepted Resume File Types:

.pdf  
.docx  

Recommended Upload Limit:

5 MB maximum file size

---

# Frontend Responsibilities

The frontend should:
- show loading indicators during API requests
- display error messages for failed requests
- validate file type before uploading resumes
- handle null resume preview values safely
- support empty search results

---

# Backend Responsibilities

The backend should:
- always return JSON responses
- avoid returning HTML error pages
- provide clear error messages for invalid requests
- maintain stable request and response formats during development

---

# Team Agreement

To prevent frontend/backend integration issues:

1. Endpoint names will remain:
   POST /upload-resume  
   POST /search  
   GET /jobs  
   GET /health

2. Request and response field names will remain stable unless the team agrees to changes.

3. Backend changes affecting request or response structures must be communicated before implementation.

4. Frontend API responses must follow this contract.
