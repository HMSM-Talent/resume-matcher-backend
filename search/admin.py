from django.contrib import admin
from .models import JobListing, JobApplication

@admin.register(JobListing)
class JobListingAdmin(admin.ModelAdmin):
    list_display = ('job_description', 'company', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('job_description__title', 'company__company_name')

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('job_listing', 'candidate', 'status', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('job_listing__job_description__title', 'candidate__email')
