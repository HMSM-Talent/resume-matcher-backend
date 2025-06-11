from django.urls import path
from .views import ResumeUploadView, JobDescriptionUploadView, SimilarityScoreListView, DebugView, JobDescriptionView

urlpatterns = [
    path('upload/resume/', ResumeUploadView.as_view(), name='resume-upload'),
    path('upload/job-description/', JobDescriptionUploadView.as_view(), name='job-description-upload'),
    path('similarity-scores/', SimilarityScoreListView.as_view(), name='similarity-scores'),
    path('debug/', DebugView.as_view(), name='debug'),
    path('job-descriptions/<int:id>/', JobDescriptionView.as_view(), name='job-description-detail'),
]