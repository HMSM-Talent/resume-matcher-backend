import os
from rest_framework import serializers
from .models import Resume, JobDescription, JobApplication


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
    job_type = serializers.CharField(required=False)
    experience_level = serializers.CharField(required=False)
    file_url = serializers.SerializerMethodField()
    similarity_score = serializers.FloatField(read_only=True, required=False)
    application_status = serializers.CharField(read_only=True, required=False)

    class Meta:
        model = JobDescription
        fields = [
            'id', 'user', 'file', 'file_url', 'uploaded_at', 'extracted_text',
            'title', 'company_name', 'location', 'job_type',
            'experience_level', 'required_skills', 'is_active',
            'created_at', 'updated_at', 'similarity_score', 'application_status'
        ]
        read_only_fields = ['id', 'uploaded_at', 'user', 'extracted_text', 'created_at', 'updated_at', 
                           'similarity_score', 'application_status']

    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

    def validate_file(self, file):
        ext = os.path.splitext(file.name)[1]
        if ext.lower() != '.pdf':
            raise serializers.ValidationError("Only PDF files are allowed.")
        return file

    def validate_job_type(self, value):
        if not value:
            return value
            
        # Convert to uppercase and replace hyphen with underscore
        value = value.upper().replace('-', '_')
        
        # Map common variations
        job_type_mapping = {
            'FULLTIME': 'FULL_TIME',
            'PARTTIME': 'PART_TIME',
            'FULL_TIME': 'FULL_TIME',
            'PART_TIME': 'PART_TIME',
            'CONTRACT': 'CONTRACT',
            'INTERNSHIP': 'INTERNSHIP',
            'REMOTE': 'REMOTE'
        }
        
        mapped_value = job_type_mapping.get(value)
        if not mapped_value:
            raise serializers.ValidationError(
                f"Invalid job type. Must be one of: {', '.join(job_type_mapping.values())}"
            )
        return mapped_value

    def validate_experience_level(self, value):
        if not value:
            return value
            
        # Convert to uppercase
        value = value.upper()
        
        # Map common variations
        level_mapping = {
            'ENTRY': 'ENTRY',
            'MID': 'MID',
            'SENIOR': 'SENIOR',
            'LEAD': 'LEAD',
            'MANAGER': 'MANAGER',
            'JUNIOR': 'ENTRY',
            'MID_LEVEL': 'MID',
            'SENIOR_LEVEL': 'SENIOR',
            'LEAD_LEVEL': 'LEAD',
            'MANAGER_LEVEL': 'MANAGER'
        }
        
        mapped_value = level_mapping.get(value)
        if not mapped_value:
            raise serializers.ValidationError(
                f"Invalid experience level. Must be one of: {', '.join(level_mapping.values())}"
            )
        return mapped_value

    def validate(self, attrs):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            attrs['user'] = request.user
            if not request.user.is_company:
                raise serializers.ValidationError("Only company accounts can upload job descriptions.")
        return attrs


class JobApplicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)
    company_name = serializers.CharField(source='job.company_name', read_only=True)
    candidate_email = serializers.CharField(source='candidate.email', read_only=True)
    
    class Meta:
        model = JobApplication
        fields = ['id', 'job', 'job_title', 'company_name', 'candidate', 'candidate_email', 
                 'applied_at', 'status']
        read_only_fields = ['candidate', 'applied_at', 'status']
    
    def validate(self, attrs):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            attrs['candidate'] = request.user
            if not request.user.is_candidate:
                raise serializers.ValidationError("Only candidates can apply for jobs.")
        return attrs