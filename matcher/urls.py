from django.urls import path
from .views import match_resumes_to_jd

urlpatterns = [
    path('match/', match_resumes_to_jd, name='match-resumes'),
]