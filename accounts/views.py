from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from .serializers import (
    UserSerializer,
    CandidateRegistrationSerializer,
    CompanyRegistrationSerializer
)
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

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
        user = self.request.user
        logger.info(f"UserDetailView - User: {user.email}")
        logger.info(f"UserDetailView - Role: {user.role}")
        logger.info(f"UserDetailView - Is authenticated: {user.is_authenticated}")
        logger.info(f"UserDetailView - Is company: {user.is_company}")
        logger.info(f"UserDetailView - Is admin: {user.is_admin}")
        logger.info(f"UserDetailView - Auth header: {self.request.headers.get('Authorization', 'No auth header')}")
        return user

    def get(self, request, *args, **kwargs):
        try:
            response = super().get(request, *args, **kwargs)
            logger.info(f"UserDetailView - Response data: {response.data}")
            return response
        except Exception as e:
            logger.error(f"UserDetailView - Error: {str(e)}", exc_info=True)
            raise

class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(email=request.data['email'])
            response.data['user'] = UserSerializer(user).data
        return response