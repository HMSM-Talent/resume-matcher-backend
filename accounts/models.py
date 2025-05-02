from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    USER_TYPE_CHOICES = (
        ('candidate', 'Candidate'),
        ('company', 'Company'),
    )
    
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    phone_number = models.CharField(max_length=15, blank=True)
    
    # Company specific fields
    company_name = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=50, blank=True)
    company_size = models.CharField(max_length=20, blank=True)
    
    # Candidate specific fields
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # email & password are required by default
    
    def __str__(self):
        if self.user_type == 'company':
            return self.company_name
        return f"{self.first_name} {self.last_name}" 