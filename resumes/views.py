from django.shortcuts import render
from rest_framework import generics, permissions
from .models import Resume, JobDescription
from .serializers import ResumeSerializer, JobDescriptionSerializer
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class ResumeUploadView(generics.CreateAPIView):
    queryset = Resume.objects.all()
    serializer_class = ResumeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@method_decorator(csrf_exempt, name='dispatch')
class JobDescriptionUploadView(generics.CreateAPIView):
    queryset = JobDescription.objects.all()
    serializer_class = JobDescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(company=self.request.user)
