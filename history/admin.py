from django.contrib import admin
from .models import UserHistory

@admin.register(UserHistory)
class UserHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'action_type', 'status', 'company_name', 'job_title', 'created_at')
    list_filter = ('action_type', 'status', 'created_at')
    search_fields = ('user__email', 'company_name', 'job_title', 'description')
    ordering = ('-created_at',)
