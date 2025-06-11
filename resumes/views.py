from rest_framework import generics, permissions, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
import logging
import re # Import re module

from .models import Resume, JobDescription
from matcher.models import SimilarityScore
from search.models import JobListing
from .serializers import ResumeSerializer, JobDescriptionSerializer
from matcher.serializers import SimilarityScoreSerializer
from matcher.utils import extract_text_from_file, calculate_similarity

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


# Helper function to extract job details
def _extract_job_details_from_text(text: str) -> dict:
    title = None
    company_name = None
    location = None

    # Max length for CharFields
    MAX_LENGTH = 200

    logger.debug(f"Attempting to extract details from text (first 500 chars): {text[:500]}...")

    # Improved regex for title: looks for common job titles, usually at the start of a line or sentence.
    # More restrictive about what follows the job title itself.
    title_match = re.search(r"^(?:(?:senior|junior|lead|staff|principal|associate|entry level|mid level|senior level|lead level|manager level)\s+)?([a-zA-Z0-9\s\.\-\/,]{5,150}?)(?:\s+at|\s+for|\s+in|$)", text, re.IGNORECASE | re.MULTILINE)
    if title_match:
        title = title_match.group(1).strip()
        logger.debug(f"Title regex matched: '{title}'")
        if title and len(title) > MAX_LENGTH: # Truncate if too long
            title = title[:MAX_LENGTH]
            logger.debug(f"Title truncated to: '{title}'")

    # Improved regex for company name: looks for common company name indicators, often capitalized.
    # Focuses on capturing a single line or phrase.
    company_name_match = re.search(r"(?:at|for|by|company):?\s*([A-Z][a-zA-Z0-9\s&.,\-']{3,150}?)(?:\s+(?:Inc|LLC|Corp|GmbH|Ltd|Group|Solutions|Technologies|Innovations|Services|Partners|Advisory|Consulting|Labs|Ventures|Systems))?\b", text, re.IGNORECASE)
    if company_name_match:
        company_name = company_name_match.group(1).strip()
        logger.debug(f"Company name regex matched: '{company_name}'")
        if company_name and len(company_name) > MAX_LENGTH: # Truncate if too long
            company_name = company_name[:MAX_LENGTH]
            logger.debug(f"Company name truncated to: '{company_name}'")

    # Improved regex for location: looks for city, state, country patterns, often capitalized.
    # More focused on typical location formats.
    location_match = re.search(r"(?:location|based in|office in|work from):?\s*([A-Z][a-zA-Z\s.,\-]{3,150}?)(?:,\s*[A-Z]{2})?(?:,\s*[A-Z][a-zA-Z]+)?(?:,\s*\b(?:USA|United States|Canada|UK|United Kingdom|Germany|France|India|Australia))?\b", text, re.IGNORECASE)
    if location_match:
        location = location_match.group(1).strip()
        logger.debug(f"Location regex matched: '{location}'")
        if location and len(location) > MAX_LENGTH: # Truncate if too long
            location = location[:MAX_LENGTH]
            logger.debug(f"Location truncated to: '{location}'")

    logger.debug(f"Extracted details - Title: '{title}', Company: '{company_name}', Location: '{location}'")

    return {
        'title': title,
        'company_name': company_name,
        'location': location
    }


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
            
            # Extract structured details from the text
            extracted_details = _extract_job_details_from_text(extracted_text)
            instance.title = extracted_details.get('title')
            instance.company_name = extracted_details.get('company_name')
            instance.location = extracted_details.get('location')

            instance.save() # Save again after updating details
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

            # Create a JobListing for this job description
            JobListing.objects.create(
                job_description=instance,
                company=request.user,
                is_active=True
            )
            logger.info(f"Created JobListing for JobDescription {instance.id}")

            return Response({
                "message": f"{self.model_class.__name__} uploaded and processed successfully.",
                "extracted_text": extracted_text,
                "title": instance.title,
                "company_name": instance.company_name,
                "location": instance.location,
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            instance.delete() # Delete the instance if processing fails
            logger.error(f"Error processing job description upload: {str(e)}", exc_info=True)
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


class JobDescriptionListView(generics.ListAPIView):
    serializer_class = JobDescriptionSerializer
    permission_classes = [IsCompanyOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        'job_type': ['exact'],
        'experience_level': ['exact'],
        'location': ['exact', 'icontains'],
        'is_active': ['exact'],
    }
    ordering_fields = ['uploaded_at', 'title']
    ordering = ['-uploaded_at']

    def get_queryset(self):
        user = self.request.user
        logger.info(f"Getting job descriptions for company: {user.id} ({user.email})")
        
        # Base queryset - only get job descriptions for this company
        qs = JobDescription.objects.filter(user=user)
        logger.info(f"Found {qs.count()} job descriptions for company")
        
        return qs


class JobDescriptionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = JobDescription.objects.all()
    serializer_class = JobDescriptionSerializer
    permission_classes = [IsCompanyOrAdmin]

    def get_queryset(self):
        # Ensure a company can only retrieve, update, or delete their own job descriptions
        if self.request.user.is_company:
            return self.queryset.filter(user=self.request.user)
        return self.queryset.none()