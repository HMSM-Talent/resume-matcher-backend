from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def match_resumes_to_jd(request):
    user = request.user  # This gives you the currently authenticated user

    return Response({
        "message": "Resume–JD similarity logic will be implemented later.",
        "user": {
            "id": user.id,
            "email": user.email,
            "user_type": user.user_type,
        }
    })