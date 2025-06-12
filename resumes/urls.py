from django.urls import path
from .views import (
    ResumeUploadView, JobDescriptionUploadView, SimilarityScoreListView, 
    DebugView, JobDescriptionView, JobDescriptionListView, JobDescriptionSearchView,
    apply_for_job, JobApplicationListView,
    ApplicationHistoryView, WithdrawApplicationView, CompanyDashboardView,
    CompanyHistoryView
)

urlpatterns = [
    path('upload/resume/', ResumeUploadView.as_view(), name='resume-upload'),
    path('upload/job-description/', JobDescriptionUploadView.as_view(), name='job-description-upload'),
    path('similarity-scores/', SimilarityScoreListView.as_view(), name='similarity-scores'),
    path('debug/', DebugView.as_view(), name='debug'),
    path('job-descriptions/', JobDescriptionListView.as_view(), name='job-descriptions-list'),
    path('job-descriptions/search/', JobDescriptionSearchView.as_view(), name='job-descriptions-search'),
    path('job-descriptions/<int:id>/', JobDescriptionView.as_view(), name='job-description-detail'),
    path('job-descriptions/<int:job_id>/apply/', apply_for_job, name='apply-for-job'),
    path('job-applications/', JobApplicationListView.as_view(), name='job-applications-list'),
    path('applications/history/', ApplicationHistoryView.as_view(), name='application-history'),
    path('applications/<int:pk>/withdraw/', WithdrawApplicationView.as_view(), name='withdraw-application'),
    path('company/dashboard/', CompanyDashboardView.as_view(), name='company-dashboard'),
    path('company/history/', CompanyHistoryView.as_view(), name='company-history'),
]