from django.urls import path
from .views import ResumeUploadView, JobDescriptionUploadView

urlpatterns = [
    path('upload-resume/', ResumeUploadView.as_view(), name='upload-resume'),
    path('upload-jd/', JobDescriptionUploadView.as_view(), name='upload-jd'),
]