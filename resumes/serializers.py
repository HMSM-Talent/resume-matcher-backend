from rest_framework import serializers
from .models import Resume, JobDescription


class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['id', 'user', 'file', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at', 'user']

class JobDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobDescription
        fields = ['id', 'file', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']