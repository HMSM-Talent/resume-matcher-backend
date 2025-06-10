"""URL configuration for the matcher app, handling similarity matching endpoints."""

from django.urls import path
from .views import SimilarityView

urlpatterns = [
    path('similarity/', SimilarityView.as_view(), name='similarity'),
]