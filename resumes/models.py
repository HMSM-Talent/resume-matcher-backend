import os
from datetime import datetime
import magic  # For MIME type detection
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator

# ──────── Validators ────────

def validate_file_size(value):
    if value.size > 10 * 1024 * 1024:
        raise ValidationError("Maximum file size is 10MB.")

def validate_file_content(value):
    if value.size == 0:
        raise ValidationError("File cannot be empty.")

    mime_type = magic.from_buffer(value.read(1024), mime=True)
    value.seek(0)

    if mime_type != 'application/pdf':
        raise ValidationError("Only PDF files are allowed.")

    try:
        if not value.read(5).startswith(b'%PDF-'):
            raise ValidationError("Invalid PDF file.")
        value.seek(0)
    except Exception:
        raise ValidationError("Unable to read PDF header. Ensure it's a valid PDF file.")

# ──────── Upload Paths ────────

def get_resume_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'resumes/{instance.user.id}/{timestamp}{ext}'

def get_jd_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'jds/{instance.user.id}/{timestamp}{ext}'

# ──────── Models ────────

class Resume(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(
        upload_to=get_resume_upload_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf']),
            validate_file_size,
            validate_file_content
        ]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    extracted_text = models.TextField(blank=True, null=True)
    original_filename = models.CharField(max_length=255, blank=True)

    def clean(self):
        if not self.user.is_candidate:
            raise ValidationError("Only candidates can upload resumes.")

    def save(self, *args, **kwargs):
        if not self.original_filename and self.file:
            self.original_filename = os.path.basename(self.file.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} - Resume ({self.original_filename})"


class JobDescription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(
        upload_to=get_jd_upload_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf']),
            validate_file_size,
            validate_file_content
        ]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    extracted_text = models.TextField(blank=True, null=True)
    original_filename = models.CharField(max_length=255, blank=True)

    # Metadata
    title = models.CharField(max_length=200, null=True, blank=True)
    company_name = models.CharField(max_length=200, null=True, blank=True)
    location = models.CharField(max_length=200, null=True, blank=True)
    job_type = models.CharField(max_length=50, choices=[
        ('FULL_TIME', 'Full Time'),
        ('PART_TIME', 'Part Time'),
        ('CONTRACT', 'Contract'),
        ('INTERNSHIP', 'Internship'),
        ('REMOTE', 'Remote'),
    ], null=True, blank=True)
    experience_level = models.CharField(max_length=50, choices=[
        ('ENTRY', 'Entry Level'),
        ('MID', 'Mid Level'),
        ('SENIOR', 'Senior Level'),
        ('LEAD', 'Lead Level'),
        ('MANAGER', 'Manager Level'),
    ], null=True, blank=True)
    required_skills = models.TextField(
        help_text="Comma-separated list of required skills", null=True, blank=True
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if not self.user.is_company:
            raise ValidationError("Only companies can upload job descriptions.")
        if not self.title:
            raise ValidationError("Job title is required.")
        if not self.company_name:
            raise ValidationError("Company name is required.")

    def save(self, *args, **kwargs):
        if not self.original_filename and self.file:
            self.original_filename = os.path.basename(self.file.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} at {self.company_name}"

    def get_match_category(self, score):
        if score >= 0.8:
            return "High Match"
        elif score >= 0.6:
            return "Medium Match"
        else:
            return "Low Match"

class JobApplication(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('DECLINED', 'Declined'),
        ('WITHDRAWN', 'Withdrawn')
    ]
    
    job = models.ForeignKey(JobDescription, on_delete=models.CASCADE, related_name='applications')
    candidate = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    company_feedback = models.TextField(null=True, blank=True)
    similarity_score = models.FloatField(null=True)

    class Meta:
        unique_together = ('job', 'candidate')
        ordering = ['-applied_at']

    def clean(self):
        if not self.candidate.is_candidate:
            raise ValidationError("Only candidates can apply for jobs.")
        if self.job.user.is_candidate:
            raise ValidationError("Cannot apply to a job posted by a candidate.")
        if not self.job.is_active:
            raise ValidationError("Cannot apply to an inactive job posting.")

    def __str__(self):
        return f"{self.candidate.email} - {self.job.title} ({self.status})"