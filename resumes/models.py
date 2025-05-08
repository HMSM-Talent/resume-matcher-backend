from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser

User = get_user_model()

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('candidate', 'Candidate'),
        ('company', 'Company'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    
class Resume(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(upload_to='resumes/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - Resume"

class JobDescription(models.Model):
    company = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    file = models.FileField(upload_to='jds/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - Job Description"