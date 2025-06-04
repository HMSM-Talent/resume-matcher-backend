# Resume Matcher Backend

A Django-based backend service for matching resumes with job descriptions using semantic similarity.

## Features

- Resume and Job Description upload (PDF/DOCX)
- Automatic text extraction from documents
- Semantic similarity scoring between resumes and job descriptions
- Match categorization (High/Medium/Low)
- Filtering and sorting of matches
- Role-based access control (Candidate/Company/Admin)

## Prerequisites

- Python 3.11+
- pip
- virtualenv

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/resume-matcher-backend.git
cd resume-matcher-backend
```

2. Create and activate virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Create superuser (optional):
```bash
python manage.py createsuperuser
```

## Running the Server

```bash
python manage.py runserver
```

The server will start at `http://127.0.0.1:8000/`

## API Endpoints

### Authentication
- Login: `POST /api/auth/login/`
- Register: `POST /api/auth/register/`

### Resume Management
- Upload Resume: `POST /upload/resume/`
- View Resumes: `GET /resumes/`

### Job Description Management
- Upload Job Description: `POST /upload/job-description/`
- View Job Descriptions: `GET /job-descriptions/`

### Similarity Scores
- View Matches: `GET /similarity-scores/`
  - Query Parameters:
    - `limit`: Get top N matches (e.g., `?limit=5`)
    - `job_description__job_type`: Filter by job type
    - `job_description__experience_level`: Filter by experience level
    - `job_description__location`: Filter by location
    - `job_description__company_name`: Filter by company
    - `score__gte`: Filter by minimum score
    - `ordering`: Sort by score or date

## Project Structure

```
resume-matcher-backend/
├── backend/              # Project settings
├── resumes/             # Main app
│   ├── models.py        # Database models
│   ├── views.py         # API views
│   ├── serializers.py   # Data serializers
│   └── urls.py          # URL routing
├── matcher/             # Similarity matching logic
├── manage.py            # Django management script
└── requirements.txt     # Project dependencies
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

