from rest_framework import serializers
from .models import Resume, JobDescription, SimilarityScore
from django.core.exceptions import ValidationError


class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['id', 'user', 'file', 'uploaded_at', 'extracted_text']
        read_only_fields = ['id', 'uploaded_at', 'user', 'extracted_text']

    def validate_file(self, file):
        if not file.name.endswith('.pdf'):
            raise serializers.ValidationError("Only PDF files are allowed.")
        return file

    def validate(self, attrs):
        # Get the current user from the context
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            # Set the user to the current user
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
        if not file.name.endswith('.pdf'):
            raise serializers.ValidationError("Only PDF files are allowed.")
        return file

    def validate(self, attrs):
        # Get the current user from the context
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            # Set the user to the current user
            attrs['user'] = request.user
            # Validate that the user is a company
            if not request.user.is_company:
                raise serializers.ValidationError("Only company accounts can upload job descriptions.")
        return attrs

class SimilarityScoreSerializer(serializers.ModelSerializer):
    resume_user = serializers.EmailField(source='resume.user.email', read_only=True)
    jd_user = serializers.EmailField(source='job_description.user.email', read_only=True)
    match_category = serializers.SerializerMethodField()
    job_details = serializers.SerializerMethodField()

    class Meta:
        model = SimilarityScore
        fields = [
            'id', 'resume', 'job_description', 'resume_user', 'jd_user',
            'score', 'created_at', 'match_category', 'job_details'
        ]
        read_only_fields = ['id', 'score', 'created_at']

    def validate(self, attrs):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            # For companies: can only compare their own job descriptions
            if request.user.is_company:
                if attrs['job_description'].user != request.user:
                    raise serializers.ValidationError("You can only compare resumes with your own job descriptions.")
            # For candidates: can only compare their own resumes
            elif request.user.is_candidate:
                if attrs['resume'].user != request.user:
                    raise serializers.ValidationError("You can only compare your own resumes with job descriptions.")
        return attrs

    def get_match_category(self, obj):
        return obj.job_description.get_match_category(obj.score)

    def get_job_details(self, obj):
        jd = obj.job_description
        return {
            'title': jd.title,
            'company_name': jd.company_name,
            'location': jd.location,
            'job_type': jd.job_type,
            'experience_level': jd.experience_level,
            'required_skills': jd.required_skills.split(',') if jd.required_skills else []
        }