from rest_framework import generics, permissions, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
import logging

from matcher.models import SimilarityScore
from matcher.serializers import JobDescriptionSerializer, SimilarityScoreSerializer
from matcher.utils import extract_text_from_file, calculate_similarity

from .models import Resume, JobDescription
from .serializers import ResumeSerializer

logger = logging.getLogger(__name__)


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
        if not self.serializer_class:
            raise NotImplementedError("Subclasses must set serializer_class")
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        instance = serializer.save()

        try:
            logger.info(
                "Processing %s upload for user %s",
                self.model_class.__name__,
                request.user.id
            )
            if not instance.extracted_text:
                extracted_text = extract_text_from_file(instance.file)
                instance.extracted_text = extracted_text
                instance.save()
            else:
                extracted_text = instance.extracted_text
            logger.info(
                "Text extracted and saved for %s ID %s",
                self.model_class.__name__,
                instance.id
            )
            opposite_queryset = self.get_opposite_queryset()
            logger.info("Found %d opposite documents for scoring", opposite_queryset.count())

            for other in opposite_queryset:
                logger.debug("Calculating similarity between %s %s and %s %s",
                    self.model_class.__name__, instance.id,
                    other.__class__.__name__, other.id)
                score, _ = calculate_similarity(extracted_text, other.extracted_text)
                logger.info("Similarity score calculated: %s", score)

                if self.get_user_role_check() == 'candidate':
                    SimilarityScore.objects.update_or_create(
                        resume=instance,
                        job_description=other,
                        defaults={'score': score}
                    )
                    logger.info("Score saved: resume=%s, job_description=%s, score=%s",
                        instance.id, other.id, score)
                else:
                    SimilarityScore.objects.update_or_create(
                        resume=other,
                        job_description=instance,
                        defaults={'score': score}
                    )
                    logger.info("Score saved: resume=%s, job_description=%s, score=%s",
                        other.id, instance.id, score)

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except (ValueError, IOError, OSError) as e:
            logger.error("Exception during upload: %s", e, exc_info=True)
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

        serializer = ResumeSerializer(data=request.data, context={'request': request})
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

    def post(self, request):
        # Set is_active=True in the request data
        if 'is_active' not in request.data:
            request.data['is_active'] = True
            
        return super().post(request)


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
        logger.info(f"Getting similarity scores for user: {user.id} ({user.email})")
        logger.info(f"User roles - is_admin: {user.is_admin}, is_candidate: {user.is_candidate}, is_company: {user.is_company}")
        
        # Get base queryset with all scores
        qs = SimilarityScore.objects.select_related('resume', 'job_description')
        logger.info(f"Base queryset count: {qs.count()}")
        
        # Log some sample data
        if qs.exists():
            sample = qs.first()
            logger.info(f"Sample score - Resume user: {sample.resume.user_id}, JD user: {sample.job_description.user_id}")
        
        # Apply active filter
        qs = qs.filter(job_description__is_active=True)
        logger.info(f"After active filter count: {qs.count()}")
        
        # Apply role-based filters
        if user.is_admin:
            logger.info("User is admin, returning all scores")
            return qs
        elif user.is_candidate:
            filtered_qs = qs.filter(resume__user=user)
            logger.info(f"Candidate filtered count: {filtered_qs.count()}")
            if filtered_qs.exists():
                sample = filtered_qs.first()
                logger.info(f"Sample candidate score - Resume: {sample.resume_id}, JD: {sample.job_description_id}")
            return filtered_qs
        elif user.is_company:
            filtered_qs = qs.filter(job_description__user=user)
            logger.info(f"Company filtered count: {filtered_qs.count()}")
            if filtered_qs.exists():
                sample = filtered_qs.first()
                logger.info(f"Sample company score - Resume: {sample.resume_id}, JD: {sample.job_description_id}")
            return filtered_qs
            
        logger.warning("User has no role, returning empty queryset")
        return SimilarityScore.objects.none()

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        logger.info(f"Final filtered queryset count: {queryset.count()}")
        
        # Log the actual SQL query
        logger.info(f"SQL Query: {queryset.query}")
        
        limit = request.query_params.get('limit')
        if limit and limit.isdigit():
            queryset = queryset[:int(limit)]
            logger.info(f"After limit filter count: {queryset.count()}")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class DebugView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        scores = SimilarityScore.objects.select_related('resume', 'job_description')
        
        # Get all scores for this user
        if user.is_candidate:
            user_scores = scores.filter(resume__user=user)
        elif user.is_company:
            user_scores = scores.filter(job_description__user=user)
        else:
            user_scores = scores
            
        return Response({
            "user": {
                "email": user.email,
                "is_admin": user.is_admin,
                "is_candidate": user.is_candidate,
                "is_company": user.is_company
            },
            "total_scores": scores.count(),
            "user_scores": user_scores.count(),
            "sample_scores": [
                {
                    "resume_user": s.resume.user.email,
                    "jd_user": s.job_description.user.email,
                    "score": s.score
                } for s in user_scores[:5]
            ]
        })