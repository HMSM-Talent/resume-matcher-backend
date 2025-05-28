from rest_framework import serializers
from .models import Resume, JobDescription, SimilarityScore


class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['id', 'user', 'file', 'uploaded_at', 'extracted_text']
        read_only_fields = ['id', 'uploaded_at', 'user', 'extracted_text']

class JobDescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobDescription
        fields = [
            'id', 'user', 'file', 'uploaded_at', 'extracted_text',
            'title', 'company_name', 'location', 'job_type',
            'experience_level', 'required_skills', 'is_active'
        ]
        read_only_fields = ['id', 'uploaded_at', 'user', 'extracted_text']

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