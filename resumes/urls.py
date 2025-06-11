from django.urls import path
from .views import (
    ResumeUploadView, JobDescriptionUploadView, SimilarityScoreListView, 
    DebugView, JobDescriptionView, JobDescriptionListView, JobDescriptionSearchView,
    apply_for_job, JobApplicationListView
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
]