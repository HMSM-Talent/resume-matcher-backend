from rest_framework import serializers
from .models import UserHistory

class UserHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserHistory
        fields = [
            'id', 'action_type', 'status', 'description', 
            'company_name', 'job_title', 'job_description',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at'] 