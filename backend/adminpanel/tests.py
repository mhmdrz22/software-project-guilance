from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from tasks.models import Task
from django.test import override_settings

User = get_user_model()

@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class AdminPanelTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email="admin@example.com",
            password="adminpass",
            username="admin"
        )
        self.user = User.objects.create_user(
            email="user@example.com",
            password="userpass",
            username="user"
        )
        self.overview_url = "/api/admin/overview/"
        self.notify_url = "/api/admin/notify/"

    def test_overview_requires_admin(self):
        self.client.force_authenticate(user=self.user)
        resp = self.client.get(self.overview_url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_overview_returns_open_tasks_count(self):
        # Create tasks for the regular user
        Task.objects.create(user=self.user, title="t1", status="TODO")
        Task.objects.create(user=self.user, title="t2", status="DOING")
        Task.objects.create(user=self.user, title="t3", status="DONE")

        self.client.force_authenticate(user=self.admin)
        resp = self.client.get(self.overview_url)

        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        users = resp.data["users"]
        user_row = next(u for u in users if u["email"] == self.user.email)
        # TODO and DOING should count as open (2 tasks)
        self.assertEqual(user_row["open_tasks_count"], 2)

    def test_notify_enqueues_email_job(self):
        self.client.force_authenticate(user=self.admin)
        payload = {"recipients": [self.user.email], "message": "Hello from admin"}
        resp = self.client.post(self.notify_url, payload, format="json")

        self.assertEqual(resp.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn("job_id", resp.data)
        self.assertEqual(resp.data["recipients_count"], 1)

    def test_notify_ignores_invalid_recipients(self):
        self.client.force_authenticate(user=self.admin)
        payload = {"recipients": ["ghost@example.com"], "message": "Hello ghost"}
        resp = self.client.post(self.notify_url, payload, format="json")

        # Should fail as no valid recipients found
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
