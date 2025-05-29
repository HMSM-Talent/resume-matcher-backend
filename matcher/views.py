from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import SimilarityRequestSerializer
from matcher.utils import calculate_similarity, get_match_category

import logging

logger = logging.getLogger(__name__)

class SimilarityView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            serializer = SimilarityRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            resume_text = serializer.validated_data['resume_text']
            jd_text = serializer.validated_data['job_description_text']

            # Calculate similarity with caching
            similarity_score, analysis = calculate_similarity(resume_text, jd_text)
            match_category = get_match_category(similarity_score)

            return Response({
                "similarity_score": round(float(similarity_score), 4),
                "match_category": match_category,
                "analysis": analysis
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            logger.error(f"Validation error in similarity calculation: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Unexpected error in similarity calculation: {str(e)}")
            return Response(
                {"error": "An unexpected error occurred while calculating similarity"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )