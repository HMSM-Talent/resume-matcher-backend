# Resume Matcher Backend

A Django-based backend service for matching resumes with job descriptions using semantic similarity. This service provides a robust API for resume and job description management, with advanced matching capabilities using machine learning.

## Features

- Resume and Job Description upload (PDF/DOCX)
- Automatic text extraction from documents
- Semantic similarity scoring between resumes and job descriptions
- Match categorization (High/Medium/Low)
- Filtering and sorting of matches
- Role-based access control (Candidate/Company/Admin)
- RESTful API with JWT authentication
- File storage with AWS S3 support
- Production-ready configuration

## Prerequisites

- Python 3.11.8 (as specified in .python-version)
- PostgreSQL 15+
- pip
- virtualenv
- AWS Account (for S3 storage)
- Hugging Face account (for model access)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/resume-matcher-backend.git
cd resume-matcher-backend
```

2. Create and activate virtual environment:
```bash
# On Windows
python -m venv .venv
.venv\Scripts\activate

# On Linux/Mac
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the project root with the following variables:
```env
# Django settings
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database settings
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# AWS S3 settings
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_STORAGE_BUCKET_NAME=your_bucket_name
AWS_S3_REGION_NAME=your_region
AWS_S3_CUSTOM_DOMAIN=your-custom-domain.com

# JWT settings
JWT_SECRET_KEY=your-jwt-secret
JWT_ACCESS_TOKEN_LIFETIME=5
JWT_REFRESH_TOKEN_LIFETIME=1

# Model settings
MODEL_PATH=/path/to/phi-2.Q4_K_M.gguf
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create superuser:
```bash
python manage.py createsuperuser
```

7. Collect static files:
```bash
python manage.py collectstatic
```

## Development Setup

1. Set `DEBUG=True` in `.env`
2. Use SQLite for development:
```env
DATABASE_URL=sqlite:///db.sqlite3
```

3. Run development server:
```bash
python manage.py runserver
```

## Production Deployment

1. Set up a production server (e.g., AWS EC2, DigitalOcean)
2. Install required system packages:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.11 python3.11-venv postgresql postgresql-contrib nginx

# CentOS/RHEL
sudo yum update
sudo yum install python3.11 postgresql-server postgresql-contrib nginx
```

3. Configure PostgreSQL:
```bash
sudo -u postgres psql
CREATE DATABASE your_db_name;
CREATE USER your_db_user WITH PASSWORD 'your_db_password';
GRANT ALL PRIVILEGES ON DATABASE your_db_name TO your_db_user;
```

4. Set up Nginx:
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /path/to/your/staticfiles/;
    }

    location /media/ {
        alias /path/to/your/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

5. Set up Gunicorn:
```bash
gunicorn backend.wsgi:application --bind 127.0.0.1:8000 --workers 3 --timeout 120
```

6. Set up systemd service:
```ini
[Unit]
Description=Resume Matcher Backend
After=network.target

[Service]
User=your_user
Group=your_group
WorkingDirectory=/path/to/resume-matcher-backend
Environment="PATH=/path/to/resume-matcher-backend/.venv/bin"
ExecStart=/path/to/resume-matcher-backend/.venv/bin/gunicorn backend.wsgi:application --bind 127.0.0.1:8000 --workers 3 --timeout 120

[Install]
WantedBy=multi-user.target
```

## API Documentation

### Authentication Endpoints

- Register Candidate: `POST /api/auth/candidate/register/`
  ```json
  {
    "email": "user@example.com",
    "password": "your_password",
    "password2": "your_password",
    "first_name": "John",
    "last_name": "Doe",
    "profile": {
      "phone_number": "+1234567890"  // Optional
    }
  }
  ```

- Register Company: `POST /api/auth/company/register/`
  ```json
  {
    "email": "company@example.com",
    "password": "your_password",
    "password2": "your_password",
    "profile": {
      "company_name": "Example Corp"
    }
  }
  ```

- Login: `POST /api/auth/login/`
  ```json
  {
    "email": "user@example.com",
    "password": "your_password"
  }
  ```

### Resume Management

- Upload Resume: `POST /api/upload/resume/`
  - Content-Type: multipart/form-data
  - Fields: file (PDF/DOCX)

- List Resumes: `GET /api/resumes/`
  - Query Parameters:
    - `ordering`: Sort by field
    - `search`: Search in extracted text

### Job Description Management

- Upload Job Description: `POST /api/upload/job-description/`
  - Content-Type: multipart/form-data
  - Fields: file (PDF), title, company_name, location, job_type, experience_level

- List Job Descriptions: `GET /api/job-descriptions/`
  - Query Parameters:
    - `is_active`: Filter active/inactive jobs
    - `job_type`: Filter by job type
    - `experience_level`: Filter by experience level

### Similarity Scores

- Get Matches: `GET /api/similarity-scores/`
  - Query Parameters:
    - `limit`: Get top N matches
    - `score__gte`: Minimum score threshold
    - `ordering`: Sort by score or date

## Project Structure

```
resume-matcher-backend/
├── accounts/              # User authentication and profiles
├── backend/              # Project settings
├── matcher/             # Similarity matching logic
├── resumes/             # Main app
├── search/              # Search functionality
├── media/               # Uploaded files
├── static/              # Static files
├── .env                 # Environment variables
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

