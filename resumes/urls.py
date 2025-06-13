from django.urls import path
from .views import (
    ResumeUploadView, JobDescriptionUploadView, SimilarityScoreListView, 
    DebugView, JobDescriptionView, JobDescriptionListView, JobDescriptionSearchView,
    apply_for_job, JobApplicationListView, ApplicationHistoryView, WithdrawApplicationView, 
    CompanyDashboardView, CompanyHistoryView, JobCloseView, UpdateApplicationStatusView
)

urlpatterns = [
    path('resumes/upload/', ResumeUploadView.as_view(), name='resume-upload'),
    path('job-descriptions/upload/', JobDescriptionUploadView.as_view(), name='job-description-upload'),
    path('similarity-scores/', SimilarityScoreListView.as_view(), name='similarity-scores-list'),
    path('debug/', DebugView.as_view(), name='debug'),
    path('job-descriptions/<uuid:id>/', JobDescriptionView.as_view(), name='job-description-detail'),
    path('job-descriptions/', JobDescriptionListView.as_view(), name='job-description-list'),
    path('job-descriptions/search/', JobDescriptionSearchView.as_view(), name='job-description-search'),
    path('job-descriptions/<uuid:job_id>/apply/', apply_for_job, name='apply-for-job'),
    path('job-applications/', JobApplicationListView.as_view(), name='job-applications-list'),
    path('applications/history/', ApplicationHistoryView.as_view(), name='application-history'),
    path('applications/<uuid:pk>/withdraw/', WithdrawApplicationView.as_view(), name='withdraw-application'),
    path('applications/<uuid:application_id>/update-status/', UpdateApplicationStatusView.as_view(), name='update-application-status'),
    path('company/dashboard/', CompanyDashboardView.as_view(), name='company-dashboard'),
    path('company/history/', CompanyHistoryView.as_view(), name='company-history'),
    path('job-descriptions/<uuid:job_id>/close/', JobCloseView.as_view(), name='close-job'),
]