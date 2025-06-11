from django.urls import path
from .views import ResumeUploadView, JobDescriptionUploadView, SimilarityScoreListView, DebugView, JobDescriptionListView, JobDescriptionDetailView

urlpatterns = [
    path('upload/resume/', ResumeUploadView.as_view(), name='resume-upload'),
    path('upload/job-description/', JobDescriptionUploadView.as_view(), name='job-description-upload'),
    path('similarity-scores/', SimilarityScoreListView.as_view(), name='similarity-scores'),
    path('job-descriptions/', JobDescriptionListView.as_view(), name='job-descriptions'),
    path('job-descriptions/<int:pk>/', JobDescriptionDetailView.as_view(), name='job-description-detail'),
    path('debug/', DebugView.as_view(), name='debug'),
]