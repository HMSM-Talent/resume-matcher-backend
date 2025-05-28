from django.db import models
from django.conf import settings  # for AUTH_USER_MODEL
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

def validate_file_size(value):
    filesize = value.size
    if filesize > 10 * 1024 * 1024:  # 10MB limit
        raise ValidationError("Maximum file size is 10MB")

class Resume(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)            
    file = models.FileField(
        upload_to='resumes/',
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'docx']),
            validate_file_size
        ]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    extracted_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.email} - Resume"

class JobDescription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(
        upload_to='jds/',
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'docx']),
            validate_file_size
        ]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    extracted_text = models.TextField(blank=True, null=True)
    
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
    score = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('resume', 'job_description')
        ordering = ['-score']

    def __str__(self):
        return f"Score: {self.score:.2f} - {self.resume} vs {self.job_description}"