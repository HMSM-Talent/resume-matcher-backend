import os
from rest_framework import serializers
from .models import Resume, JobDescription, JobApplication
from matcher.models import SimilarityScore
import logging
from django.conf import settings

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
    company_name = serializers.CharField(required=False)
    required_skills = serializers.CharField(required=False)
    file_url = serializers.SerializerMethodField()
    score = serializers.FloatField(read_only=True, required=False, allow_null=True)
    application_status = serializers.CharField(read_only=True, required=False)

    class Meta:
        model = JobDescription
        fields = [
            'id', 'user', 'file', 'file_url',
            'title', 'company_name', 'location', 'job_type',
            'experience_level', 'required_skills', 'is_active',
            'created_at', 'updated_at', 'score', 'application_status'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at', 
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
    job_title = serializers.CharField(source='job.title', read_only=True)
    company_name = serializers.CharField(source='job.company_name', read_only=True)
    user = serializers.SerializerMethodField()
    applied_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S.%fZ', read_only=True)
    updated_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S.%fZ', read_only=True)

    class Meta:
        model = JobApplication
        fields = [
            'id', 'job', 'user', 'job_title', 'company_name',
            'status', 'applied_at', 'updated_at', 'similarity_score',
            'company_feedback'
        ]
        read_only_fields = ['id', 'applied_at', 'updated_at', 'similarity_score']

    def get_user(self, obj):
        if obj.resume and obj.resume.user:
            return {
                'id': obj.resume.user.id,
                'email': obj.resume.user.email,
                'first_name': obj.resume.user.first_name,
                'last_name': obj.resume.user.last_name
            }
        return None

    def get_similarity_score(self, obj):
        try:
            score = SimilarityScore.objects.filter(
                job_description=obj.job,
                resume__user=obj.user['id']
            ).order_by('-created_at').first()
            
            if score:
                return round(score.score * 100, 2)
            return None
        except Exception as e:
            logger.error(f"Error getting similarity score for application {obj.id}: {str(e)}")
            return None


class ApplicationHistorySerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source='job.title', read_only=True)
    company_name = serializers.CharField(source='job.company_name', read_only=True)
    job_file_url = serializers.SerializerMethodField()
    applied_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S.%fZ', read_only=True)
    updated_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S.%fZ', read_only=True)
    similarity_score = serializers.SerializerMethodField()
    company_feedback = serializers.CharField(read_only=True, allow_null=True)

    class Meta:
        model = JobApplication
        fields = [
            'id', 'job', 'job_title', 'company_name', 'job_file_url',
            'status', 'applied_at', 'updated_at', 'similarity_score',
            'company_feedback'
        ]
        read_only_fields = fields

    def get_job_file_url(self, obj):
        if obj.job and obj.job.file:
            return obj.job.file.url
        return None

    def get_similarity_score(self, obj):
        try:
            # Get the latest similarity score for this application
            score = SimilarityScore.objects.filter(
                job_description=obj.job,
                resume=obj.resume
            ).order_by('-created_at').first()
            
            if score:
                return round(score.score * 100, 2)
            return None
        except Exception as e:
            logger.error(f"Error getting similarity score for application {obj.id}: {str(e)}")
            return None


class ApplicationCountSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    high_match = serializers.IntegerField()
    medium_match = serializers.IntegerField()
    low_match = serializers.IntegerField()


class CandidateSerializer(serializers.ModelSerializer):
    class Meta:
        model = settings.AUTH_USER_MODEL
        fields = ['id', 'email', 'first_name', 'last_name']


class ApplicationSerializer(serializers.ModelSerializer):
    candidate = CandidateSerializer(source='resume.user')
    match_score = serializers.SerializerMethodField()
    match_category = serializers.SerializerMethodField()
    status = serializers.CharField()
    applied_at = serializers.DateTimeField(source='created_at')

    class Meta:
        model = JobApplication
        fields = ['id', 'candidate', 'match_score', 'match_category', 'status', 'applied_at']

    def get_match_score(self, obj):
        try:
            score = SimilarityScore.objects.filter(
                job_description=obj.job,
                resume=obj.resume
            ).order_by('-created_at').first()
            
            if score:
                return round(score.score * 100, 2)
            return None
        except Exception as e:
            logger.error(f"Error getting similarity score for application {obj.id}: {str(e)}")
            return None

    def get_match_category(self, obj):
        score = self.get_match_score(obj)
        if score is not None:
            score = score / 100  # Convert back to decimal
            if score >= 0.8:
                return "High Match"
            elif score >= 0.6:
                return "Medium Match"
            else:
                return "Low Match"
        return None


class JobDashboardSerializer(serializers.ModelSerializer):
    application_counts = serializers.SerializerMethodField()
    applications = ApplicationSerializer(many=True)
    created_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S.%fZ', read_only=True)
    updated_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S.%fZ', read_only=True)
    closed_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S.%fZ', read_only=True)
    close_reason = serializers.CharField(read_only=True)

    class Meta:
        model = JobDescription
        fields = [
            'id', 'title', 'company_name', 'location', 'job_type',
            'experience_level', 'is_active', 'created_at', 'updated_at',
            'closed_at', 'close_reason', 'application_counts', 'applications'
        ]

    def get_application_counts(self, obj):
        applications = obj.applications.all()
        total = applications.count()
        
        # Get all similarity scores for this job's applications
        similarity_scores = SimilarityScore.objects.filter(
            job_description=obj,
            resume__in=applications.values_list('resume', flat=True)
        ).select_related('resume')
        
        # Count applications by score ranges
        high_match = similarity_scores.filter(score__gte=0.8).count()
        medium_match = similarity_scores.filter(score__gte=0.6, score__lt=0.8).count()
        low_match = similarity_scores.filter(score__lt=0.6).count()
        
        return {
            'total': total,
            'high_match': high_match,
            'medium_match': medium_match,
            'low_match': low_match
        }


class CompanyDashboardSerializer(serializers.Serializer):
    jobs = serializers.SerializerMethodField()

    def get_jobs(self, obj):
        jobs = obj.get('jobs', [])
        return JobDashboardSerializer(jobs, many=True).data


class CompanyHistorySerializer(serializers.ModelSerializer):
    total_applications = serializers.SerializerMethodField()
    application_stats = serializers.SerializerMethodField()
    applications = serializers.SerializerMethodField()
    closed_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S.%fZ', read_only=True)
    created_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S.%fZ', read_only=True)
    updated_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S.%fZ', read_only=True)

    class Meta:
        model = JobDescription
        fields = [
            'id', 'title', 'company_name', 'location', 'job_type',
            'experience_level', 'required_skills', 'is_active',
            'created_at', 'updated_at', 'closed_at', 'close_reason',
            'total_applications', 'application_stats', 'applications'
        ]

    def get_applications(self, obj):
        applications = obj.applications.select_related(
            'resume', 'resume__user', 'resume__user__candidate_profile'
        ).order_by('-created_at')
        return JobApplicationSerializer(applications, many=True).data

    def get_total_applications(self, obj):
        return obj.applications.count()

    def get_application_stats(self, obj):
        applications = obj.applications.all()
        
        # Get all similarity scores for this job's applications
        similarity_scores = SimilarityScore.objects.filter(
            job_description=obj,
            resume__in=applications.values_list('resume', flat=True)
        )
        
        # Count applications by score ranges
        high_match = similarity_scores.filter(score__gte=0.8).count()
        medium_match = similarity_scores.filter(score__gte=0.6, score__lt=0.8).count()
        low_match = similarity_scores.filter(score__lt=0.6).count()
        
        return {
            'total': applications.count(),
            'high_match': high_match,
            'medium_match': medium_match,
            'low_match': low_match
        }


class JobCloseSerializer(serializers.ModelSerializer):
    reason = serializers.CharField(write_only=True, required=False)
    closed_at = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S.%fZ', read_only=True)
    close_reason = serializers.CharField(read_only=True)

    class Meta:
        model = JobDescription
        fields = ['id', 'is_active', 'closed_at', 'close_reason', 'reason']
        read_only_fields = ['id', 'is_active', 'closed_at']