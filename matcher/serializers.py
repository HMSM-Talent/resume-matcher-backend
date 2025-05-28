from rest_framework import serializers

class SimilarityRequestSerializer(serializers.Serializer):
    resume_text = serializers.CharField()
    job_description_text = serializers.CharField()