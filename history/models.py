from django.db import models
from django.conf import settings

# Create your models here.

class UserHistory(models.Model):
    class ActionType(models.TextChoices):
        RESUME_UPLOAD = 'RESUME_UPLOAD', 'Resume Upload'
        JOB_APPLICATION = 'JOB_APPLICATION', 'Job Application'
        JOB_POST = 'JOB_POST', 'Job Post'
        PROFILE_UPDATE = 'PROFILE_UPDATE', 'Profile Update'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        REVIEWING = 'REVIEWING', 'Reviewing'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        REJECTED = 'REJECTED', 'Rejected'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='history')
    action_type = models.CharField(max_length=20, choices=ActionType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    description = models.TextField()
    company_name = models.CharField(max_length=255, blank=True, null=True)
    job_title = models.CharField(max_length=255, blank=True, null=True)
    job_description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'history'
        ordering = ['-created_at']
        verbose_name_plural = 'User Histories'

    def __str__(self):
        return f"{self.user.email} - {self.action_type} - {self.created_at}"
