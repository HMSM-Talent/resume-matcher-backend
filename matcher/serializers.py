from rest_framework import serializers
from resumes.models import Resume, JobDescription, SimilarityScore

class SimilarityRequestSerializer(serializers.Serializer):
    resume_text = serializers.CharField()
    job_description_text = serializers.CharField()

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
        if not request:
            raise serializers.ValidationError("Request context is required for validation.")

        user = request.user
        
        # For companies: can only compare their own job descriptions
        if user.is_company:
            if attrs['job_description'].user != user:
                raise serializers.ValidationError("You can only compare resumes with your own job descriptions.")
        
        # For candidates: can only compare their own resumes
        elif user.is_candidate:
            if attrs['resume'].user != user:
                raise serializers.ValidationError("You can only compare your own resumes with job descriptions.")
        
        # Admins can compare anything
        elif not user.is_admin:
            raise serializers.ValidationError("You don't have permission to perform this action.")

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

class ResumeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['id', 'user', 'file', 'uploaded_at', 'extracted_text']
        read_only_fields = ['id', 'uploaded_at', 'user', 'extracted_text']

    def validate(self, attrs):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is required for validation.")

        user = request.user
        if not user.is_candidate and not user.is_admin:
            raise serializers.ValidationError("Only candidates can upload resumes.")

        attrs['user'] = user
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

    def validate(self, attrs):
        request = self.context.get('request')
        if not request:
            raise serializers.ValidationError("Request context is required for validation.")

        user = request.user
        if not user.is_company and not user.is_admin:
            raise serializers.ValidationError("Only companies can upload job descriptions.")

        attrs['user'] = user
        return attrs