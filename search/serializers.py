from rest_framework import serializers
from .models import JobListing, JobApplication
from resumes.serializers import JobDescriptionSerializer
from accounts.serializers import UserSerializer

class JobListingSerializer(serializers.ModelSerializer):
    job_description = JobDescriptionSerializer()
    company = UserSerializer()
    
    class Meta:
        model = JobListing
        fields = [
            'id',
            'job_description',
            'company',
            'is_active',
            'created_at',
            'updated_at'
        ]

class JobApplicationSerializer(serializers.ModelSerializer):
    job_listing = JobListingSerializer()
    candidate = UserSerializer()
    
    class Meta:
        model = JobApplication
        fields = [
            'id',
            'job_listing',
            'candidate',
            'status',
            'applied_at',
            'updated_at'
        ]
        read_only_fields = ['candidate', 'applied_at', 'updated_at'] 