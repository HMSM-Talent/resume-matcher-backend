# Resume Matcher Backend API Documentation

## Authentication
All endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

## Endpoints

### 1. Resume Upload
```
POST /api/upload/resume/
```
**Request:**
- Content-Type: multipart/form-data
- Body:
  - file: PDF or DOCX file
  - title: string (optional)
  - skills: string (optional)

**Response:**
```json
{
    "id": 1,
    "user": "user@email.com",
    "file": "resumes/resume.pdf",
    "title": "Software Engineer Resume",
    "skills": "Python, Django, React",
    "extracted_text": "Full text content...",
    "created_at": "2024-03-20T10:00:00Z"
}
```

### 2. Job Description Upload
```
POST /api/upload/job-description/
```
**Request:**
- Content-Type: multipart/form-data
- Body:
  - file: PDF or DOCX file
  - title: string
  - company_name: string
  - location: string
  - job_type: string (choices: full-time, part-time, contract, internship)
  - experience_level: string (choices: entry, mid, senior, lead)
  - required_skills: string

**Response:**
```json
{
    "id": 1,
    "user": "company@email.com",
    "file": "jds/job.pdf",
    "title": "Senior Software Engineer",
    "company_name": "Tech Corp",
    "location": "New York, NY",
    "job_type": "full-time",
    "experience_level": "senior",
    "required_skills": "Python, Django, React",
    "extracted_text": "Full text content...",
    "created_at": "2024-03-20T10:00:00Z"
}
```

### 3. Similarity Scores
```
GET /api/similarity-scores/
```
**Query Parameters:**
- job_type: string (filter by job type)
- experience_level: string (filter by experience level)
- min_score: float (filter by minimum similarity score)
- limit: integer (limit number of results)

**Response:**
```json
[
    {
        "id": 1,
        "resume": {
            "id": 1,
            "user_email": "candidate@email.com",
            "title": "Software Engineer Resume"
        },
        "job_description": {
            "id": 1,
            "user_email": "company@email.com",
            "title": "Senior Software Engineer",
            "company_name": "Tech Corp",
            "job_type": "full-time",
            "experience_level": "senior"
        },
        "score": 0.85,
        "created_at": "2024-03-20T10:00:00Z"
    }
]
```

## Data Models

### Resume
```python
{
    "id": integer,
    "user": string (email),
    "file": string (file path),
    "title": string,
    "skills": string,
    "extracted_text": string,
    "created_at": datetime
}
```

### JobDescription
```python
{
    "id": integer,
    "user": string (email),
    "file": string (file path),
    "title": string,
    "company_name": string,
    "location": string,
    "job_type": string,
    "experience_level": string,
    "required_skills": string,
    "extracted_text": string,
    "created_at": datetime
}
```

### SimilarityScore
```python
{
    "id": integer,
    "resume": integer (Resume ID),
    "job_description": integer (JobDescription ID),
    "score": float,
    "created_at": datetime
}
```

## File Types
- Supported formats: PDF, DOCX
- Maximum file size: 10MB

## Error Responses
```json
{
    "error": "Error message",
    "detail": "Detailed error information"
}
```

## Rate Limiting
- 100 requests per hour per user
- 1000 requests per hour per IP

## CORS
- Allowed origins: Configured in settings
- Allowed methods: GET, POST, OPTIONS
- Allowed headers: Content-Type, Authorization 