from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import UserHistory
from .serializers import UserHistorySerializer

class UserHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action_type', 'status']
    search_fields = ['company_name', 'job_title', 'description']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return UserHistory.objects.all()
        return UserHistory.objects.filter(user=user)

    @action(detail=False, methods=['get'])
    def my_history(self, request):
        """Get the current user's history"""
        history = UserHistory.objects.filter(user=request.user)
        serializer = self.get_serializer(history, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def recent_activity(self, request):
        """Get recent activity for the current user"""
        history = UserHistory.objects.filter(user=request.user).order_by('-created_at')[:10]
        serializer = self.get_serializer(history, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def by_action_type(self, request):
        """Get history filtered by action type"""
        action_type = request.query_params.get('action_type', None)
        if action_type:
            history = UserHistory.objects.filter(
                user=request.user,
                action_type=action_type
            )
            serializer = self.get_serializer(history, many=True)
            return Response(serializer.data)
        return Response({"error": "action_type parameter is required"}, status=400)
