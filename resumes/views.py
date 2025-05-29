from rest_framework import generics, permissions, filters
from rest_framework.exceptions import PermissionDenied
from .models import Resume, JobDescription, SimilarityScore
from .serializers import ResumeSerializer, JobDescriptionSerializer, SimilarityScoreSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from matcher.utils import extract_text_from_file, calculate_similarity
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend

class IsCandidateOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.is_candidate or request.user.is_admin)

class IsCompanyOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (request.user.is_company or request.user.is_admin)

class ResumeUploadView(APIView):
    permission_classes = [IsCandidateOrAdmin]

    def post(self, request):
        serializer = ResumeSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            resume = serializer.save()

            resume_file = resume.file
            try:
                text = extract_text_from_file(resume_file)
                resume.extracted_text = text
                resume.save()

                # Calculate similarity with all active job descriptions
                job_descriptions = JobDescription.objects.filter(
                    extracted_text__isnull=False,
                    is_active=True
                )
                for jd in job_descriptions:
                    score = calculate_similarity(text, jd.extracted_text)
                    SimilarityScore.objects.update_or_create(
                        resume=resume,
                        job_description=jd,
                        defaults={'score': score}
                    )

                return Response({
                    "message": "Resume uploaded successfully.",
                    "extracted_text": text
                }, status=201)
            except Exception as e:
                # Delete the uploaded file if text extraction fails
                resume.delete()
                return Response({"error": str(e)}, status=400)

        return Response(serializer.errors, status=400)

class JobDescriptionUploadView(APIView):
    permission_classes = [IsCompanyOrAdmin]

    def post(self, request):
        serializer = JobDescriptionSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            jd = serializer.save()

            jd_file = jd.file
            try:
                text = extract_text_from_file(jd_file)
                jd.extracted_text = text
                jd.save()

                # Calculate similarity with all resumes
                resumes = Resume.objects.filter(extracted_text__isnull=False)
                for resume in resumes:
                    score = calculate_similarity(resume.extracted_text, text)
                    SimilarityScore.objects.update_or_create(
                        resume=resume,
                        job_description=jd,
                        defaults={'score': score}
                    )

                return Response({
                    "message": "Job description uploaded successfully.",
                    "extracted_text": text
                }, status=201)
            except Exception as e:
                # Delete the uploaded file if text extraction fails
                jd.delete()
                return Response({"error": str(e)}, status=400)

        return Response(serializer.errors, status=400)

class SimilarityScoreListView(generics.ListAPIView):
    serializer_class = SimilarityScoreSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        'job_description__job_type': ['exact'],
        'job_description__experience_level': ['exact'],
        'job_description__location': ['exact', 'icontains'],
        'job_description__company_name': ['exact', 'icontains'],
        'score': ['gte', 'lte'],
    }
    ordering_fields = ['score', 'created_at']
    ordering = ['-score']  # Default ordering by score descending

    def get_queryset(self):
        user = self.request.user
        queryset = SimilarityScore.objects.select_related(
            'resume', 'job_description'
        ).filter(job_description__is_active=True)

        if user.is_admin:
            return queryset
        elif user.is_candidate:
            return queryset.filter(resume__user=user)
        elif user.is_company:
            return queryset.filter(job_description__user=user)
        return SimilarityScore.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        # Handle limit parameter
        limit = request.query_params.get('limit')
        if limit and limit.isdigit():
            queryset = queryset[:int(limit)]
        
        # Apply pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)