from django.urls import path
from .views import SimilarityView

urlpatterns = [
    path('similarity/', SimilarityView.as_view(), name='similarity'),
]