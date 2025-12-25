from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Task

User = get_user_model()

class TaskModelTest(TestCase):
    def setUp(self):
        """Set up a user for the tests."""
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123",
        )

    def test_create_task_with_defaults(self):
        """Test creating a task with default status and priority."""
        task = Task.objects.create(
            user=self.user,
            title="A simple test task",
        )
        self.assertEqual(task.title, "A simple test task")
        self.assertEqual(task.user, self.user)
        self.assertEqual(task.status, "TODO")
        self.assertEqual(task.priority, "MEDIUM")
        self.assertIsNone(task.due_date)
        self.assertEqual(str(task), "A simple test task")

    def test_create_task_with_specific_values(self):
        """Test creating a task with specific status, priority, and due date."""
        task = Task.objects.create(
            user=self.user,
            title="A high priority task",
            description="This is important.",
            status="DOING",
            priority="HIGH",
        )
        self.assertEqual(task.title, "A high priority task")
        self.assertEqual(task.status, "DOING")
        self.assertEqual(task.priority, "HIGH")
        self.assertEqual(task.description, "This is important.")

    def test_task_ordering(self):
        """Test that tasks are ordered by creation date in descending order."""
        task1 = Task.objects.create(user=self.user, title="First Task")
        task2 = Task.objects.create(user=self.user, title="Second Task")

        tasks = Task.objects.all()
        self.assertEqual(tasks[0], task2)
        self.assertEqual(tasks[1], task1)


class TaskAPITest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="user1", email="user1@example.com", password="password123"
        )
        self.user2 = User.objects.create_user(
            username="user2", email="user2@example.com", password="password123"
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user1)

        self.task1 = Task.objects.create(user=self.user1, title="User 1's Task")
        self.task2 = Task.objects.create(user=self.user2, title="User 2's Task")

    def test_list_tasks_for_authenticated_user(self):
        """Test that a user can only list their own tasks."""
        response = self.client.get("/api/tasks/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], self.task1.title)

    def test_create_task(self):
        """Test that a user can create a task."""
        data = {"title": "New Task", "priority": "HIGH"}
        response = self.client.post("/api/tasks/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Task.objects.filter(user=self.user1).count(), 2)

    def test_retrieve_own_task(self):
        """Test that a user can retrieve their own task."""
        response = self.client.get(f"/api/tasks/{self.task1.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.task1.title)

    def test_cannot_retrieve_other_users_task(self):
        """Test that a user cannot retrieve another user's task."""
        response = self.client.get(f"/api/tasks/{self.task2.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_own_task(self):
        """Test that a user can update their own task."""
        data = {"title": "Updated Title", "status": "DONE"}
        response = self.client.put(f"/api/tasks/{self.task1.id}/", data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.task1.refresh_from_db()
        self.assertEqual(self.task1.title, "Updated Title")
        self.assertEqual(self.task1.status, "DONE")

    def test_delete_own_task(self):
        """Test that a user can delete their own task."""
        response = self.client.delete(f"/api/tasks/{self.task1.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=self.task1.id).exists())

    def test_unauthenticated_user_cannot_access_tasks(self):
        """Test that an unauthenticated user gets a 401 error."""
        self.client.logout()
        response = self.client.get("/api/tasks/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
