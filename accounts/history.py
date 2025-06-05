from django.db import models
from .models import CustomUser

class UserHistory(models.Model):
    class ActionType(models.TextChoices):
        LOGIN = 'login', 'Login'
        LOGOUT = 'logout', 'Logout'
        PROFILE_UPDATE = 'profile_update', 'Profile Update'
        RESUME_UPLOAD = 'resume_upload', 'Resume Upload'
        RESUME_UPDATE = 'resume_update', 'Resume Update'
        JOB_APPLICATION = 'job_application', 'Job Application'
        JOB_POST = 'job_post', 'Job Post'
        JOB_UPDATE = 'job_update', 'Job Update'
        MATCH_VIEW = 'match_view', 'Match View'
        MATCH_ACTION = 'match_action', 'Match Action'

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='history')
    action_type = models.CharField(max_length=20, choices=ActionType.choices)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)  # For storing additional data

    class Meta:
        verbose_name_plural = 'User Histories'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.action_type} - {self.created_at}" 