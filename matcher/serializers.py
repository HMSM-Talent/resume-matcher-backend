from rest_framework import serializers
from resumes.models import JobDescription
from matcher.models import SimilarityScore
from resumes.utils import extract_text_from_file
from matcher.llm import extract_job_metadata


class SimilarityRequestSerializer(serializers.Serializer):
    resume_text = serializers.CharField()
    job_description_text = serializers.CharField()


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

        # Run LLM metadata extraction if file exists
        file = attrs.get("file")
        if file:
            try:
                extracted_text = extract_text_from_file(file)
                attrs['extracted_text'] = extracted_text

                meta = extract_job_metadata(extracted_text)

                attrs['title'] = attrs.get('title') or meta.get("Job Title")
                attrs['company_name'] = attrs.get('company_name') or meta.get("Company Name")
                attrs['location'] = attrs.get('location') or meta.get("Location")
                attrs['job_type'] = attrs.get('job_type') or meta.get("Job Type")
                attrs['experience_level'] = attrs.get('experience_level') or meta.get("Experience Level")
                attrs['required_skills'] = attrs.get('required_skills') or ",".join(meta.get("Required Skills", []))
            except Exception as e:
                raise serializers.ValidationError(f"LLM metadata extraction failed: {str(e)}")

        return attrs


class SimilarityScoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimilarityScore
        fields = ['id', 'resume', 'job_description', 'score', 'created_at']
        read_only_fields = fields