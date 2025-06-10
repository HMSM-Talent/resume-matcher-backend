from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from .models import JobListing, JobApplication
from resumes.models import JobDescription
from .serializers import JobListingSerializer, JobApplicationSerializer

@api_view(['GET'])
@permission_classes([AllowAny])
def job_search(request):
    query = request.GET.get('q', '')
    job_listings = JobListing.objects.filter(is_active=True)
    
    if query:
        job_listings = job_listings.filter(
            Q(job_description__title__icontains=query) |
            Q(job_description__description__icontains=query) |
            Q(company__company_name__icontains=query)
        )
    
    # Pagination
    paginator = Paginator(job_listings, 10)  # Show 10 jobs per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    serializer = JobListingSerializer(page_obj, many=True)
    
    return Response({
        'count': paginator.count,
        'next': page_obj.has_next() and f"?page={page_obj.next_page_number()}" or None,
        'previous': page_obj.has_previous() and f"?page={page_obj.previous_page_number()}" or None,
        'results': serializer.data
    })

@api_view(['GET'])
@permission_classes([AllowAny])
def job_detail(request, job_id):
    job_listing = get_object_or_404(JobListing, id=job_id, is_active=True)
    has_applied = False
    
    if request.user.is_authenticated and request.user.is_candidate:
        has_applied = JobApplication.objects.filter(
            job_listing=job_listing,
            candidate=request.user
        ).exists()
    
    serializer = JobListingSerializer(job_listing)
    data = serializer.data
    data['has_applied'] = has_applied
    
    return Response(data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_job(request, job_id):
    if not request.user.is_candidate:
        return Response(
            {"error": "Only candidates can apply for jobs."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    job_listing = get_object_or_404(JobListing, id=job_id, is_active=True)
    
    # Check if already applied
    if JobApplication.objects.filter(job_listing=job_listing, candidate=request.user).exists():
        return Response(
            {"error": "You have already applied for this job."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create new application
    application = JobApplication.objects.create(
        job_listing=job_listing,
        candidate=request.user
    )
    
    serializer = JobApplicationSerializer(application)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_applications(request):
    if not request.user.is_candidate:
        return Response(
            {"error": "Only candidates can view their applications."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    applications = JobApplication.objects.filter(candidate=request.user).order_by('-applied_at')
    serializer = JobApplicationSerializer(applications, many=True)
    return Response(serializer.data)
