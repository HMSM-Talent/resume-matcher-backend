from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from .serializers import SimilarityRequestSerializer
from matcher.utils import extract_text_from_file

# Load model once globally
model = SentenceTransformer('all-mpnet-base-v2')

class SimilarityView(APIView):
    def post(self, request):
        serializer = SimilarityRequestSerializer(data=request.data)
        if serializer.is_valid():
            resume_text = serializer.validated_data['resume_text']
            jd_text = serializer.validated_data['job_description_text']

            # Encode text
            embeddings = model.encode([resume_text, jd_text])
            sim_score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]

            return Response({"similarity_score": round(float(sim_score), 4)}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)