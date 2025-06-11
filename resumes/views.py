from rest_framework import generics, permissions, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
import logging

from .models import Resume, JobDescription, JobApplication
from matcher.models import SimilarityScore
from .serializers import ResumeSerializer, JobDescriptionSerializer, JobApplicationSerializer
from matcher.serializers import SimilarityScoreSerializer
from matcher.utils import extract_text_from_file, calculate_similarity
from django.db import models

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
        serializer = self.get_serializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        instance = serializer.save()

        try:
            logger.info(f"Processing {self.model_class.__name__} upload for user {request.user.id}")
            extracted_text = extract_text_from_file(instance.file)
            instance.extracted_text = extracted_text
            instance.save()
            logger.info(f"Text extracted and saved for {self.model_class.__name__} ID {instance.id}")

            opposite_queryset = self.get_opposite_queryset()
            logger.info(f"Found {opposite_queryset.count()} opposite documents for scoring")

            for other in opposite_queryset:
                logger.debug(f"Calculating similarity between {self.model_class.__name__} {instance.id} and {other.__class__.__name__} {other.id}")
                score, _ = calculate_similarity(extracted_text, other.extracted_text)
                logger.info(f"Similarity score calculated: {score}")

                if self.get_user_role_check() == 'candidate':
                    SimilarityScore.objects.update_or_create(
                        resume=instance,
                        job_description=other,
                        defaults={'score': score}
                    )
                    logger.info(f"Score saved: resume={instance.id}, job_description={other.id}, score={score}")
                else:
                    SimilarityScore.objects.update_or_create(
                        resume=other,
                        job_description=instance,
                        defaults={'score': score}
                    )
                    logger.info(f"Score saved: resume={other.id}, job_description={instance.id}, score={score}")

            return Response({
                "message": f"{self.model_class.__name__} uploaded and processed successfully.",
                "extracted_text": extracted_text
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Exception during upload: {e}", exc_info=True)
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

    def post(self, request):
        # Set is_active=True in the request data
        if 'is_active' not in request.data:
            request.data['is_active'] = True
            
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        instance = serializer.save()

        try:
            logger.info(f"Processing {self.model_class.__name__} upload for user {request.user.id}")
            extracted_text = extract_text_from_file(instance.file)
            instance.extracted_text = extracted_text
            instance.save()
            logger.info(f"Text extracted and saved for {self.model_class.__name__} ID {instance.id}")

            opposite_queryset = self.get_opposite_queryset()
            logger.info(f"Found {opposite_queryset.count()} opposite documents for scoring")

            for other in opposite_queryset:
                logger.debug(f"Calculating similarity between {self.model_class.__name__} {instance.id} and {other.__class__.__name__} {other.id}")
                score, _ = calculate_similarity(extracted_text, other.extracted_text)
                logger.info(f"Similarity score calculated: {score}")

                SimilarityScore.objects.update_or_create(
                    resume=other,
                    job_description=instance,
                    defaults={'score': score}
                )
                logger.info(f"Score saved: resume={other.id}, job_description={instance.id}, score={score}")

            return Response({
                "message": f"{self.model_class.__name__} uploaded and processed successfully.",
                "extracted_text": extracted_text,
                "title": instance.title,
                "company_name": instance.company_name,
                "location": instance.location,
                "job_type": instance.job_type,
                "experience_level": instance.experience_level,
                "file_url": request.build_absolute_uri(instance.file.url) if instance.file else None
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            logger.error(f"Exception during upload: {e}", exc_info=True)
            instance.delete()
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


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

class JobDescriptionView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        try:
            job_description = JobDescription.objects.get(id=id)
            # Check if user has permission to view this job description
            if not (request.user.is_admin or 
                   request.user.is_company and job_description.user == request.user or
                   request.user.is_candidate and job_description.is_active):
                return Response(
                    {'error': 'You do not have permission to view this job description'}, 
                    status=status.HTTP_403_FORBIDDEN
                )

            data = {
                'id': job_description.id,
                'title': job_description.title,
                'company_name': job_description.company_name,
                'location': job_description.location,
                'job_type': job_description.job_type,
                'experience_level': job_description.experience_level,
                'required_skills': job_description.required_skills,
                'file_url': request.build_absolute_uri(job_description.file.url) if job_description.file else None,
                'is_active': job_description.is_active,
                'created_at': job_description.created_at,
                'updated_at': job_description.updated_at
            }
            return Response(data)
        except JobDescription.DoesNotExist:
            return Response(
                {'error': 'Job description not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class JobDescriptionListView(generics.ListAPIView):
    serializer_class = JobDescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['job_type', 'experience_level', 'is_active']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return JobDescription.objects.all()
        elif user.is_company:
            return JobDescription.objects.filter(user=user)
        elif user.is_candidate:
            return JobDescription.objects.filter(is_active=True)
        return JobDescription.objects.none()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class JobDescriptionSearchView(generics.ListAPIView):
    serializer_class = JobDescriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['job_type', 'experience_level', 'location']
    search_fields = ['title', 'company_name', 'required_skills', 'location']
    ordering_fields = ['created_at', 'title', 'score_value']
    ordering = ['-created_at']  # Default sort by date

    def get_queryset(self):
        user = self.request.user
        if not user.is_candidate:
            return JobDescription.objects.none()

        # Get active job descriptions
        queryset = JobDescription.objects.filter(is_active=True)

        # Get the candidate's resume
        try:
            resume = Resume.objects.get(user=user)
            if resume and resume.extracted_text:
                # Calculate similarity scores and store them in a dictionary
                score_dict = {}
                for job in queryset:
                    if job.extracted_text:
                        try:
                            # Calculate similarity using the same algorithm as Candidate Dashboard
                            score, _ = calculate_similarity(resume.extracted_text, job.extracted_text)
                            score_dict[job.id] = score
                        except Exception as e:
                            logger.error(f"Error calculating similarity score: {str(e)}")
                            score_dict[job.id] = 0.0
                    else:
                        score_dict[job.id] = 0.0

                # Apply minimum score filter if specified
                min_score = self.request.query_params.get('min_score')
                if min_score:
                    try:
                        min_score = float(min_score)
                        job_ids = [job_id for job_id, score in score_dict.items() if score >= min_score]
                        queryset = queryset.filter(id__in=job_ids)
                    except (TypeError, ValueError):
                        pass

                # Get application status for each job
                applications = JobApplication.objects.filter(
                    job__in=queryset,
                    candidate=user
                ).values_list('job_id', 'status')
                application_dict = dict(applications)

                # Add application status and score to each job
                for job in queryset:
                    job.application_status = application_dict.get(job.id)
                    job.score = score_dict.get(job.id, 0.0)

                # Always annotate with score_value for consistent sorting
                queryset = queryset.annotate(
                    score_value=models.Case(
                        *[models.When(id=job_id, then=models.Value(score)) 
                          for job_id, score in score_dict.items()],
                        default=models.Value(0),
                        output_field=models.FloatField(),
                    )
                )

                # Sort by specified field
                sort_by = self.request.query_params.get('sort_by', 'date')
                if sort_by == 'score':
                    queryset = queryset.order_by(
                        models.F('score_value').desc(nulls_last=True),
                        '-created_at'  # Secondary sort by date for jobs with same score
                    )
                else:  # default to date
                    queryset = queryset.order_by('-created_at')

        except Resume.DoesNotExist:
            # If no resume exists, set score to None for all jobs
            queryset = queryset.annotate(
                score_value=models.Value(None, output_field=models.FloatField())
            ).order_by(
                models.F('score_value').desc(nulls_last=True),
                '-created_at'  # Secondary sort by date for jobs without scores
            )
            for job in queryset:
                job.score = None

        return queryset

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def apply_for_job(request, job_id):
    try:
        job = JobDescription.objects.get(id=job_id)
        
        # Check if already applied
        if JobApplication.objects.filter(job=job, candidate=request.user).exists():
            return Response(
                {'detail': 'You have already applied for this job.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create new application
        application = JobApplication.objects.create(
            job=job,
            candidate=request.user
        )
        
        serializer = JobApplicationSerializer(application)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except JobDescription.DoesNotExist:
        return Response(
            {'detail': 'Job not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error applying for job: {str(e)}", exc_info=True)
        return Response(
            {'detail': 'An error occurred while processing your application.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class JobApplicationListView(generics.ListAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'job__job_type', 'job__experience_level']
    ordering_fields = ['applied_at', 'status']
    ordering = ['-applied_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return JobApplication.objects.all()
        elif user.is_company:
            return JobApplication.objects.filter(job__user=user)
        elif user.is_candidate:
            return JobApplication.objects.filter(candidate=user)
        return JobApplication.objects.none()