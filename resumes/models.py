from django.db import models
from django.conf import settings  # for AUTH_USER_MODEL
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import os
from datetime import datetime
import magic  # for file type detection

def validate_file_size(value):
    filesize = value.size
    if filesize > 10 * 1024 * 1024:  # 10MB limit
        raise ValidationError("Maximum file size is 10MB")

def validate_file_content(value):
    # Get file extension
    ext = os.path.splitext(value.name)[1].lower()
    
    # Check if file is empty
    if value.size == 0:
        raise ValidationError("File cannot be empty")
    
    # Read the first few bytes of the file to check its type
    file_mime = magic.from_buffer(value.read(1024), mime=True)
    value.seek(0)  # Reset file pointer
    
    # Check if it's a PDF
    if file_mime != 'application/pdf':
        raise ValidationError("Only PDF files are allowed. Please upload a PDF file.")
    
    # Check if PDF is valid
    try:
        # Try to read the PDF header
        header = value.read(5)
        value.seek(0)  # Reset file pointer
        if not header.startswith(b'%PDF-'):
            raise ValidationError("Invalid PDF file. Please upload a valid PDF file.")
    except Exception as e:
        raise ValidationError("Error reading PDF file. Please ensure it's a valid PDF file.")

def get_resume_upload_path(instance, filename):
    # Get file extension
    ext = os.path.splitext(filename)[1]
    # Create path: resumes/user_id/timestamp_filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'resumes/{instance.user.id}/{timestamp}{ext}'

def get_jd_upload_path(instance, filename):
    # Get file extension
    ext = os.path.splitext(filename)[1]
    # Create path: jds/user_id/timestamp_filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return f'jds/{instance.user.id}/{timestamp}{ext}'

class Resume(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)            
    file = models.FileField(
        upload_to=get_resume_upload_path,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf']),  # Only allow PDF
            validate_file_size,
            validate_file_content
        ]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    extracted_text = models.TextField(blank=True, null=True)
    original_filename = models.CharField(max_length=255, blank=True)

    def clean(self):
        super().clean()
        if not self.user.is_candidate:
            raise ValidationError("Only candidates can upload resumes")

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
            FileExtensionValidator(allowed_extensions=['pdf']),  # Only allow PDF
            validate_file_size,
            validate_file_content
        ]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    extracted_text = models.TextField(blank=True, null=True)
    original_filename = models.CharField(max_length=255, blank=True)
    
    # Additional metadata fields
    title = models.CharField(max_length=200, null=True, blank=True)
    company_name = models.CharField(max_length=200, null=True, blank=True)
    location = models.CharField(max_length=200, null=True, blank=True)
    job_type = models.CharField(max_length=50, choices=[
        ('FULL_TIME', 'Full Time'),
        ('PART_TIME', 'Part Time'),
        ('CONTRACT', 'Contract'),
        ('INTERNSHIP', 'Internship'),
        ('REMOTE', 'Remote')
    ], null=True, blank=True)
    experience_level = models.CharField(max_length=50, choices=[
        ('ENTRY', 'Entry Level'),
        ('MID', 'Mid Level'),
        ('SENIOR', 'Senior Level'),
        ('LEAD', 'Lead Level'),
        ('MANAGER', 'Manager Level')
    ], null=True, blank=True)
    required_skills = models.TextField(help_text="Comma-separated list of required skills", null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def clean(self):
        super().clean()
        if not self.user.is_company:
            raise ValidationError("Only companies can upload job descriptions")
        if not self.title:
            raise ValidationError("Job title is required")
        if not self.company_name:
            raise ValidationError("Company name is required")

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

class SimilarityScore(models.Model):
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name='similarity_scores')
    job_description = models.ForeignKey(JobDescription, on_delete=models.CASCADE, related_name='similarity_scores')
    score = models.FloatField(
        validators=[
            MinValueValidator(0.0, message="Score cannot be less than 0"),
            MaxValueValidator(1.0, message="Score cannot be greater than 1")
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('resume', 'job_description')
        ordering = ['-score']
        indexes = [
            models.Index(fields=['resume', 'job_description']),
            models.Index(fields=['score']),
        ]

    def clean(self):
        super().clean()
        if self.score < 0 or self.score > 1:
            raise ValidationError("Score must be between 0 and 1")

    def __str__(self):
        return f"Score: {self.score:.2f} - {self.resume} vs {self.job_description}"