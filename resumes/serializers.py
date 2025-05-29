import os
from rest_framework import serializers
from .models import Resume, JobDescription


class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['id', 'user', 'file', 'uploaded_at', 'extracted_text']
        read_only_fields = ['id', 'uploaded_at', 'user', 'extracted_text']

    def validate_file(self, file):
        # Check file size (max 5MB)
        if file.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("File size must be no more than 5MB")
        
        # Check file extension
        ext = os.path.splitext(file.name)[1]
        if ext.lower() not in ['.pdf', '.doc', '.docx']:
            raise serializers.ValidationError("Only PDF and Word documents are allowed")
        
        return file

    def validate(self, attrs):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            attrs['user'] = request.user
        return attrs


class JobDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobDescription
        fields = [
            'id', 'user', 'file', 'uploaded_at', 'extracted_text',
            'title', 'company_name', 'location', 'job_type',
            'experience_level', 'required_skills', 'is_active'
        ]
        read_only_fields = ['id', 'uploaded_at', 'user', 'extracted_text']

    def validate_file(self, file):
        ext = os.path.splitext(file.name)[1]
        if ext.lower() != '.pdf':
            raise serializers.ValidationError("Only PDF files are allowed.")
        return file

    def validate(self, attrs):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            attrs['user'] = request.user
            if not request.user.is_company:
                raise serializers.ValidationError("Only company accounts can upload job descriptions.")
        return attrs