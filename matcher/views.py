from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def match_resumes_to_jd(request):
    # Placeholder response
    return Response({
        "message": "Resume–JD similarity logic will be implemented later."
    })