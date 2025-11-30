from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Task
from .serializers import TaskSerializer


@extend_schema_view(
    list=extend_schema(summary="List my tasks", description="Returns tasks belonging to the authenticated user."),
    create=extend_schema(summary="Create a new task"),
    retrieve=extend_schema(summary="Get a single task by ID"),
    update=extend_schema(summary="Replace a task"),
    partial_update=extend_schema(summary="Partially update a task"),
    destroy=extend_schema(summary="Delete a task"),
)
class TaskViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.filter(user=self.request.user).order_by("-created_at")

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
