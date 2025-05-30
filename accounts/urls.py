from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import UserRegistrationView, UserDetailView, CustomTokenObtainPairView

urlpatterns = [
    path('candidate/register/', UserRegistrationView.as_view(), name='candidate_register'),
    path('company/register/', UserRegistrationView.as_view(), name='company_register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', UserDetailView.as_view(), name='user_me'),    
]