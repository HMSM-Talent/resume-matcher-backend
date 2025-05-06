from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([AllowAny]) 
def match_resumes_to_jd(request):
    return Response({
        "message": "Resume–JD similarity logic will be implemented later."
    })