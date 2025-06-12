from rest_framework import generics, permissions, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
import logging
from django.utils import timezone
from datetime import datetime, time

from .models import Resume, JobDescription, JobApplication
from matcher.models import SimilarityScore
from .serializers import ResumeSerializer, JobDescriptionSerializer, JobApplicationSerializer, ApplicationHistorySerializer, CompanyDashboardSerializer, CompanyHistorySerializer, JobCloseSerializer
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

            # Extract company name and required skills if not provided
            if not instance.company_name:
                # Try to extract company name from the text
                # This is a simple example - you might want to use more sophisticated extraction
                instance.company_name = request.user.company_profile.company_name if hasattr(request.user, 'company_profile') else "Unknown Company"
            
            if not instance.required_skills:
                # Try to extract required skills from the text
                # This is a simple example - you might want to use more sophisticated extraction
                instance.required_skills = "Skills to be extracted from the job description"

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
@permission_classes([IsCandidateOrAdmin])
def apply_for_job(request, job_id):
    try:
        job = JobDescription.objects.get(id=job_id)
        if not job.is_active:
            return Response(
                {"error": "This job is no longer accepting applications"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if user has already applied
        existing_application = JobApplication.objects.filter(
            job=job,
            candidate=request.user
        ).first()

        if existing_application:
            return Response(
                {"error": "You have already applied for this job"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create new application
        application = JobApplication.objects.create(
            job=job,
            candidate=request.user,
            status='PENDING'
        )

        return Response({
            "message": "Application submitted successfully",
            "application_id": application.id
        }, status=status.HTTP_201_CREATED)

    except JobDescription.DoesNotExist:
        return Response(
            {"error": "Job not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class JobApplicationListView(generics.ListAPIView):
    serializer_class = JobApplicationSerializer
    permission_classes = [IsCompanyOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['status']
    search_fields = ['candidate__email', 'candidate__first_name', 'candidate__last_name']
    ordering_fields = ['created_at', 'updated_at', 'similarity_score']
    ordering = ['-created_at']

    def get_queryset(self):
        try:
            job_id = self.request.query_params.get('job_id')
            if not job_id:
                return JobApplication.objects.none()

            job = JobDescription.objects.get(id=job_id)
            if job.user != self.request.user and not self.request.user.is_admin:
                return JobApplication.objects.none()

            return JobApplication.objects.filter(
                job=job
            ).select_related(
                'candidate',
                'candidate__candidate_profile',
                'resume'
            ).prefetch_related(
                'similarity_score'
            )

        except JobDescription.DoesNotExist:
            return JobApplication.objects.none()
        except Exception as e:
            logger.error(f"Error in job applications list: {str(e)}", exc_info=True)
            return JobApplication.objects.none()


class ApplicationHistoryView(generics.ListAPIView):
    serializer_class = ApplicationHistorySerializer
    permission_classes = [IsCandidateOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_fields = ['status']
    search_fields = ['job__title', 'job__company_name']
    ordering_fields = ['applied_at', 'updated_at', 'similarity_score']
    ordering = ['-applied_at']

    def get_queryset(self):
        queryset = JobApplication.objects.filter(
            candidate=self.request.user
        ).select_related(
            'job',
            'job__user'
        ).prefetch_related(
            'job__similarity_scores',
            'job__file'  # Prefetch the job description file
        )

        # Handle date range filtering
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')

        if start_date:
            try:
                # Convert to datetime and set to start of day
                start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
                start_datetime = timezone.make_aware(
                    datetime.combine(start_datetime.date(), time.min)
                )
                queryset = queryset.filter(applied_at__gte=start_datetime)
            except ValueError:
                pass

        if end_date:
            try:
                # Convert to datetime and set to end of day
                end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
                end_datetime = timezone.make_aware(
                    datetime.combine(end_datetime.date(), time.max)
                )
                queryset = queryset.filter(applied_at__lte=end_datetime)
            except ValueError:
                pass

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'status': 'success',
            'message': 'Applications retrieved successfully',
            'data': serializer.data
        })


class WithdrawApplicationView(APIView):
    permission_classes = [IsCandidateOrAdmin]

    def post(self, request, pk):
        try:
            application = JobApplication.objects.get(id=pk)
            
            if application.candidate != request.user and not request.user.is_admin:
                return Response(
                    {"error": "You do not have permission to withdraw this application"},
                    status=status.HTTP_403_FORBIDDEN
                )

            if application.status != 'PENDING':
                return Response(
                    {"error": "Only pending applications can be withdrawn"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            application.status = 'REJECTED'
            application.save()

            return Response({
                "message": "Application withdrawn successfully"
            }, status=status.HTTP_200_OK)

        except JobApplication.DoesNotExist:
            return Response(
                {"error": "Application not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CompanyDashboardView(APIView):
    permission_classes = [IsCompanyOrAdmin]
    serializer_class = CompanyDashboardSerializer

    def get(self, request):
        try:
            # Log authentication details
            logger.info(f"Dashboard request from user: {request.user.email}")
            logger.info(f"User role: {request.user.role}")
            logger.info(f"User is authenticated: {request.user.is_authenticated}")
            logger.info(f"User is company: {request.user.is_company}")
            logger.info(f"User is admin: {request.user.is_admin}")
            logger.info(f"Auth header: {request.headers.get('Authorization', 'No auth header')}")

            # Get all active job descriptions for the company
            jobs = JobDescription.objects.filter(
                user=request.user,
                is_active=True
            ).prefetch_related(
                'applications',
                'applications__resume',
                'applications__resume__user',
                'applications__similarity_score'
            ).order_by('-created_at')

            logger.info(f"Found {jobs.count()} active jobs for user {request.user.email}")

            # Serialize the data
            serializer = self.serializer_class({'jobs': jobs})
            return Response(serializer.data)

        except Exception as e:
            logger.error(f"Error in company dashboard: {str(e)}", exc_info=True)
            return Response(
                {"error": "An error occurred while fetching the dashboard data"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CompanyHistoryView(generics.ListAPIView):
    serializer_class = CompanyHistorySerializer
    permission_classes = [IsCompanyOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active']
    search_fields = ['title', 'company_name', 'location']
    ordering_fields = ['created_at', 'total_applications']
    ordering = ['-created_at']

    def get_queryset(self):
        try:
            logger.info(f"Company history request from user: {self.request.user.email}")
            logger.info(f"Query params: {self.request.query_params}")
            
            queryset = JobDescription.objects.filter(
                user=self.request.user
            ).prefetch_related(
                'applications',
                'applications__resume',
                'applications__resume__user',
                'applications__resume__user__candidate_profile'
            )
            
            # Apply status filter if provided
            status = self.request.query_params.get('status')
            if status == 'active':
                queryset = queryset.filter(is_active=True)
            elif status == 'closed':
                queryset = queryset.filter(is_active=False)
            
            # Apply search if provided
            search = self.request.query_params.get('search')
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(company_name__icontains=search) |
                    Q(location__icontains=search)
                )
            
            logger.info(f"Found {queryset.count()} jobs for user {self.request.user.email}")
            return queryset
            
        except Exception as e:
            logger.error(f"Error in company history queryset: {str(e)}", exc_info=True)
            raise

    def list(self, request, *args, **kwargs):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            
            response_data = {
                'status': 'success',
                'message': 'Company history retrieved successfully',
                'data': serializer.data
            }
            
            logger.info(f"Returning {len(serializer.data)} jobs in history")
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Error in company history list: {str(e)}", exc_info=True)
            return Response(
                {
                    'status': 'error',
                    'message': 'Failed to retrieve company history',
                    'detail': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class JobCloseView(APIView):
    permission_classes = [IsCompanyOrAdmin]
    serializer_class = JobCloseSerializer

    def post(self, request, job_id):
        try:
            # Get the job description
            job = JobDescription.objects.get(id=job_id)

            # Check if the user is the owner of the job
            if job.user != request.user:
                return Response(
                    {"error": "You don't have permission to close this job"},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Check if the job is already closed
            if not job.is_active:
                return Response(
                    {"error": "This job is already closed"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update the job status
            job.is_active = False
            job.closed_at = timezone.now()
            job.close_reason = request.data.get('reason', '')
            job.save()

            # Notify pending applicants
            pending_applications = job.applications.filter(status='PENDING')
            for application in pending_applications:
                # TODO: Implement notification system
                pass

            # Serialize and return the response
            serializer = self.serializer_class(job)
            return Response(serializer.data)

        except JobDescription.DoesNotExist:
            return Response(
                {"error": "Job not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error closing job: {str(e)}", exc_info=True)
            return Response(
                {"error": "An error occurred while closing the job"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )