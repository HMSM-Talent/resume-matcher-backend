from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import CustomUser, CandidateProfile, CompanyProfile
from .serializers import (
    UserSerializer,
    CandidateRegistrationSerializer,
    CompanyRegistrationSerializer,
    CandidateProfileSerializer,
    CompanyProfileSerializer,
    UserHistorySerializer
)
from .history import UserHistory
from .utils import record_user_activity

User = get_user_model()

class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        """
        Determines whether to use the Candidate or Company registration serializer
        based on the URL path.
        """
        if 'candidate' in self.request.path:
            return CandidateRegistrationSerializer
        elif 'company' in self.request.path:
            return CompanyRegistrationSerializer
        else:
            raise ValueError("Unknown registration type. Expected 'candidate' or 'company' in path.")

    def create(self, request, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        refresh = RefreshToken.for_user(user)

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }, status=status.HTTP_201_CREATED)

class UserDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        # Record the profile update
        record_user_activity(
            user=request.user,
            action_type=UserHistory.ActionType.PROFILE_UPDATE,
            description="User updated their profile",
            ip_address=request.META.get('REMOTE_ADDR'),
            metadata={'updated_fields': list(request.data.keys())}
        )
        return response

class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(email=request.data['email'])
            response.data['user'] = UserSerializer(user).data
        return response

class UserHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return UserHistory.objects.all()
        return UserHistory.objects.filter(user=user)

    @action(detail=False, methods=['get'])
    def my_history(self, request):
        """Get the current user's history"""
        history = UserHistory.objects.filter(user=request.user)
        serializer = self.get_serializer(history, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def recent_activity(self, request):
        """Get recent activity for the current user"""
        history = UserHistory.objects.filter(user=request.user).order_by('-created_at')[:10]
        serializer = self.get_serializer(history, many=True)
        return Response(serializer.data)