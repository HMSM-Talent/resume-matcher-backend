from rest_framework import generics, permissions
from rest_framework.exceptions import PermissionDenied
from .models import Resume, JobDescription
from .serializers import ResumeSerializer, JobDescriptionSerializer

class ResumeUploadView(generics.CreateAPIView):
    queryset = Resume.objects.all()
    serializer_class = ResumeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if self.request.user.role != 'candidate':
            raise PermissionDenied("Only candidates can upload resumes.")
        serializer.save(user=self.request.user)

class JobDescriptionUploadView(generics.CreateAPIView):
    queryset = JobDescription.objects.all()
    serializer_class = JobDescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if self.request.user.role != 'company':
            raise PermissionDenied("Only companies can upload job descriptions.")
        serializer.save(company=self.request.user)