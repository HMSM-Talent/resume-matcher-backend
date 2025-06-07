from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserHistoryViewSet

router = DefaultRouter()
router.register(r'history', UserHistoryViewSet, basename='history')

urlpatterns = [
    path('', include(router.urls)),
] 