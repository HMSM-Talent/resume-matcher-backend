from django.contrib import admin
from .models import JobDescription

@admin.register(JobDescription)
class JobDescriptionAdmin(admin.ModelAdmin):
    list_display = ('title', 'company_name', 'location', 'job_type', 'experience_level', 'is_active', 'created_at')
    list_filter = ('job_type', 'experience_level', 'is_active', 'created_at')
    search_fields = ('title', 'company_name', 'location', 'required_skills')
    readonly_fields = ('created_at', 'updated_at', 'extracted_text')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'company_name', 'location', 'is_active')
        }),
        ('Job Details', {
            'fields': ('job_type', 'experience_level', 'required_skills')
        }),
        ('File Information', {
            'fields': ('file', 'original_filename', 'extracted_text')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
