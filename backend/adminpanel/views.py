from django.db.models import Count, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework import serializers
from django.utils.crypto import get_random_string

from accounts.models import User
from tasks.models import Task
from .permissions import IsStaffUser
from .tasks import send_admin_notification_email

class AdminOverviewView(APIView):
    permission_classes = [IsStaffUser]

    def get(self, request, *args, **kwargs):
        # Count "open" tasks. Based on Task model, open usually means TODO or DOING.
        # We will filter for status IN ['TODO', 'DOING'].
        queryset = (
            User.objects
            .all()
            .annotate(
                open_tasks_count=Count(
                    "tasks",
                    filter=Q(tasks__status__in=["TODO", "DOING"]),
                    distinct=True,
                )
            )
        )
        data = [
            {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                # Fallback if full_name exists in future or property
                "full_name": getattr(user, "full_name", ""),
                "is_active": user.is_active,
                "open_tasks_count": user.open_tasks_count,
            }
            for user in queryset
        ]
        return Response({"users": data}, status=status.HTTP_200_OK)


class AdminNotifySerializer(serializers.Serializer):
    recipients = serializers.ListField(
        child=serializers.EmailField(),
        allow_empty=False,
    )
    message = serializers.CharField()


class AdminNotifyView(APIView):
    permission_classes = [IsStaffUser]

    def post(self, request, *args, **kwargs):
        serializer = AdminNotifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipients = serializer.validated_data["recipients"]
        message = serializer.validated_data["message"]

        # Filter only existing users
        existing_users = User.objects.filter(email__in=recipients).values_list("email", flat=True)
        recipient_list = list(existing_users)

        if not recipient_list:
            return Response(
                {"detail": "No valid recipients found."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        job_id = get_random_string(32)
        # Call Celery task asynchronously
        send_admin_notification_email.delay(recipient_list, message)

        return Response(
            {"job_id": job_id, "recipients_count": len(recipient_list)},
            status=status.HTTP_202_ACCEPTED,
        )
