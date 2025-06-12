import os
from rest_framework import serializers
from .models import Resume, JobDescription, JobApplication
from matcher.models import SimilarityScore
import logging

logger = logging.getLogger(__name__)


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
    score = serializers.FloatField(read_only=True, required=False, allow_null=True)
    application_status = serializers.CharField(read_only=True, required=False)

    class Meta:
        model = JobDescription
        fields = [
            'id', 'user', 'file', 'file_url', 'uploaded_at', 'extracted_text',
            'title', 'company_name', 'location', 'job_type',
            'experience_level', 'required_skills', 'is_active',
            'created_at', 'updated_at', 'score', 'application_status'
        ]
        read_only_fields = ['id', 'uploaded_at', 'user', 'extracted_text', 'created_at', 'updated_at', 
                           'score', 'application_status']

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
    job = serializers.PrimaryKeyRelatedField(read_only=True)
    status = serializers.CharField(read_only=True)
    applied_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)

    class Meta:
        model = JobApplication
        fields = ['id', 'job', 'status', 'applied_at', 'updated_at']
        read_only_fields = fields


class ApplicationHistorySerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)
    company_name = serializers.CharField(source='job.company_name', read_only=True)
    job_description_file = serializers.SerializerMethodField()
    applied_at = serializers.DateTimeField(format='%b %d, %Y, %I:%M %p', read_only=True)
    updated_at = serializers.DateTimeField(format='%b %d, %Y, %I:%M %p', read_only=True)
    similarity_score = serializers.SerializerMethodField()
    company_feedback = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = JobApplication
        fields = [
            'id', 'job', 'job_title', 'company_name', 'job_description_file',
            'status', 'applied_at', 'updated_at', 'similarity_score',
            'company_feedback'
        ]
        read_only_fields = fields

    def get_job_description_file(self, obj):
        if obj.job and obj.job.file:
            return obj.job.file.url
        return None

    def get_similarity_score(self, obj):
        try:
            # Get the latest similarity score for this application
            score = SimilarityScore.objects.filter(
                job_description=obj.job,
                resume__user=obj.candidate
            ).order_by('-created_at').first()
            
            if score:
                return round(score.score * 100, 2)
            return None
        except Exception as e:
            logger.error(f"Error getting similarity score for application {obj.id}: {str(e)}")
            return None


class CompanyDashboardSerializer(serializers.ModelSerializer):
    total_applications = serializers.SerializerMethodField()
    pending_applications = serializers.SerializerMethodField()
    shortlisted_applications = serializers.SerializerMethodField()
    rejected_applications = serializers.SerializerMethodField()
    withdrawn_applications = serializers.SerializerMethodField()
    recent_applications = serializers.SerializerMethodField()
    top_candidates = serializers.SerializerMethodField()

    class Meta:
        model = JobDescription
        fields = [
            'id', 'title', 'total_applications', 'pending_applications',
            'shortlisted_applications', 'rejected_applications',
            'withdrawn_applications', 'recent_applications', 'top_candidates'
        ]

    def get_total_applications(self, obj):
        return obj.applications.count()

    def get_pending_applications(self, obj):
        return obj.applications.filter(status='PENDING').count()

    def get_shortlisted_applications(self, obj):
        return obj.applications.filter(status='SHORTLISTED').count()

    def get_rejected_applications(self, obj):
        return obj.applications.filter(status='REJECTED').count()

    def get_withdrawn_applications(self, obj):
        return obj.applications.filter(status='WITHDRAWN').count()

    def get_recent_applications(self, obj):
        recent_apps = obj.applications.select_related(
            'candidate', 'candidate__candidateprofile'
        ).order_by('-applied_at')[:5]
        return JobApplicationSerializer(recent_apps, many=True).data

    def get_top_candidates(self, obj):
        top_candidates = obj.applications.select_related(
            'candidate', 'candidate__candidateprofile'
        ).filter(
            similarity_score__isnull=False
        ).order_by('-similarity_score')[:5]
        return JobApplicationSerializer(top_candidates, many=True).data


class CompanyHistorySerializer(serializers.ModelSerializer):
    job_details = serializers.SerializerMethodField()
    application_history = serializers.SerializerMethodField()
    total_applications = serializers.SerializerMethodField()
    application_stats = serializers.SerializerMethodField()

    class Meta:
        model = JobDescription
        fields = [
            'id', 'job_details', 'application_history',
            'total_applications', 'application_stats'
        ]

    def get_job_details(self, obj):
        return {
            'title': obj.title,
            'company_name': obj.company_name,
            'location': obj.location,
            'job_type': obj.job_type,
            'created_at': obj.created_at,
            'is_active': obj.is_active
        }

    def get_application_history(self, obj):
        applications = obj.applications.select_related(
            'candidate', 'candidate__candidateprofile'
        ).order_by('-applied_at')
        return JobApplicationSerializer(applications, many=True).data

    def get_total_applications(self, obj):
        return obj.applications.count()

    def get_application_stats(self, obj):
        return {
            'pending': obj.applications.filter(status='PENDING').count(),
            'shortlisted': obj.applications.filter(status='SHORTLISTED').count(),
            'rejected': obj.applications.filter(status='REJECTED').count(),
            'withdrawn': obj.applications.filter(status='WITHDRAWN').count(),
            'hired': obj.applications.filter(status='HIRED').count()
        }