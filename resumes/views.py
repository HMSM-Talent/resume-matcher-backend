from rest_framework import generics, permissions, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import Resume, JobDescription
from matcher.models import SimilarityScore
from .serializers import ResumeSerializer, JobDescriptionSerializer
from matcher.serializers import SimilarityScoreSerializer
from matcher.utils import extract_text_from_file, calculate_similarity


# ──────── Permissions ────────
class IsCandidateOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_candidate or request.user.is_admin
        )


class IsCompanyOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_company or request.user.is_admin
        )


# ──────── Shared Upload View ────────
class BaseUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = None
    model_class = None

    def get_user_role_check(self):
        raise NotImplementedError("Subclasses must implement get_user_role_check()")

    def get_opposite_queryset(self):
        role = self.get_user_role_check()
        if role == 'candidate':
            return JobDescription.objects.filter(extracted_text__isnull=False, is_active=True)
        elif role == 'company':
            return Resume.objects.filter(extracted_text__isnull=False)
        return []

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        instance = serializer.save()

        try:
            extracted_text = extract_text_from_file(instance.file)
            instance.extracted_text = extracted_text
            instance.save()

            opposite_queryset = self.get_opposite_queryset()
            print(f"[DEBUG] Found {opposite_queryset.count()} opposite documents for scoring.")

            for other in opposite_queryset:
                print(f"[DEBUG] Comparing to object ID={other.id}")
                score, _ = calculate_similarity(extracted_text, other.extracted_text)
                print(f"[DEBUG] Score calculated: {score}")

                if self.get_user_role_check() == 'candidate':
                    SimilarityScore.objects.update_or_create(
                        resume=instance,
                        job_description=other,
                        defaults={'score': score}
                    )
                    print(f"[DEBUG] Score saved (resume={instance.id}, job_description={other.id})")
                else:
                    SimilarityScore.objects.update_or_create(
                        resume=other,
                        job_description=instance,
                        defaults={'score': score}
                    )
                    print(f"[DEBUG] Score saved (resume={other.id}, job_description={instance.id})")

            return Response({
                "message": f"{self.model_class.__name__} uploaded and processed successfully.",
                "extracted_text": extracted_text
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            print(f"[ERROR] Exception during upload: {e}")
            instance.delete()
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


# ──────── Upload Endpoints ────────
class ResumeUploadView(BaseUploadView):
    permission_classes = [IsCandidateOrAdmin]
    serializer_class = ResumeSerializer
    model_class = Resume

    def get_user_role_check(self):
        return 'candidate'

    def post(self, request):
        existing_resume = Resume.objects.filter(user=request.user).first()
        replaced = False

        if existing_resume:
            replaced = True
            existing_resume.delete()  # Delete previous resume and its scores (cascade)

        serializer = self.serializer_class(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        instance = serializer.save()

        try:
            extracted_text = extract_text_from_file(instance.file)
            instance.extracted_text = extracted_text
            instance.save()

            opposite_queryset = self.get_opposite_queryset()
            for other in opposite_queryset:
                score, _ = calculate_similarity(extracted_text, other.extracted_text)
                SimilarityScore.objects.update_or_create(
                    resume=instance,
                    job_description=other,
                    defaults={'score': score}
                )

            return Response({
                "message": f"{self.model_class.__name__} uploaded and processed successfully.",
                "extracted_text": extracted_text,
                "replaced": replaced
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            instance.delete()
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class JobDescriptionUploadView(BaseUploadView):
    permission_classes = [IsCompanyOrAdmin]
    serializer_class = JobDescriptionSerializer
    model_class = JobDescription

    def get_user_role_check(self):
        return 'company'


# ──────── Score List View ────────
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
    ordering = ['-score']

    def get_queryset(self):
        user = self.request.user
        qs = SimilarityScore.objects.select_related('resume', 'job_description')#.filter(
            #job_description__is_active=True)

        if user.is_admin:
            return qs
        elif user.is_candidate:
            return qs.filter(resume__user=user)
        elif user.is_company:
            return qs.filter(job_description__user=user
)
        return SimilarityScore.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        limit = request.query_params.get('limit')

        if limit and limit.isdigit():
            queryset = queryset[:int(limit)]

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)