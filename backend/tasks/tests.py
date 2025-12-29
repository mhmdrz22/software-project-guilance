from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import Task

User = get_user_model()

class TaskAPITests(APITestCase):
    def setUp(self):
        # Create two distinct users
        self.user1 = User.objects.create_user(email="user1@example.com", password="password123")
        self.user2 = User.objects.create_user(email="user2@example.com", password="password123")

        # URLs
        self.list_url = reverse("task-list")  # Assuming router basename is 'task'

    def test_create_task_happy_path(self):
        """
        Ensure authenticated user can create a task and it's assigned to them.
        """
        self.client.force_authenticate(user=self.user1)
        data = {
            "title": "Buy Milk",
            "priority": "HIGH",
            "status": "TODO"
        }
        response = self.client.post(self.list_url, data)

        # Assert 201 Created
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Assert DB count increased
        self.assertEqual(Task.objects.count(), 1)

        # Assert user ownership
        task = Task.objects.get()
        self.assertEqual(task.user, self.user1)
        self.assertEqual(task.title, "Buy Milk")

    def test_list_tasks_isolation(self):
        """
        Ensure users only see their own tasks.
        """
        # Create tasks for both users
        Task.objects.create(user=self.user1, title="User1 Task")
        Task.objects.create(user=self.user2, title="User2 Task")

        # Authenticate as User1
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_url)

        # Assert 200 OK
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Assert only 1 task returned (User1's task)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "User1 Task")

    def test_access_other_user_task_404(self):
        """
        Ensure accessing another user's task returns 404 (Security via Visibility).
        """
        # Create a task for User2
        task_user2 = Task.objects.create(user=self.user2, title="Secret Task")
        url = reverse("task-detail", args=[task_user2.id])

        # Authenticate as User1
        self.client.force_authenticate(user=self.user1)

        # Try to retrieve/update/delete User2's task
        response = self.client.get(url)

        # Assert 404 Not Found (because get_queryset filters it out)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_task_happy_path(self):
        """
        Test successful update of a task.
        """
        task = Task.objects.create(user=self.user1, title="Old Title")
        self.client.force_authenticate(user=self.user1)
        url = reverse("task-detail", args=[task.id])
        data = {"title": "New Title", "priority": "LOW"}

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        task.refresh_from_db()
        self.assertEqual(task.title, "New Title")
        self.assertEqual(task.priority, "LOW")

    def test_delete_task_happy_path(self):
        """
        Test successful deletion of a task.
        """
        task = Task.objects.create(user=self.user1, title="To Delete")
        self.client.force_authenticate(user=self.user1)
        url = reverse("task-detail", args=[task.id])

        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Task.objects.filter(id=task.id).exists())

    def test_create_task_invalid_status(self):
        """
        Test that creating task with invalid status fails validation.
        """
        self.client.force_authenticate(user=self.user1)
        data = {"title": "Bad Task", "status": "INVALID_STATUS"}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)

    def test_filter_tasks_by_status(self):
        """
        Test filtering tasks by status.
        """
        Task.objects.create(user=self.user1, title="Todo Task", status="TODO")
        Task.objects.create(user=self.user1, title="Done Task", status="DONE")

        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_url, {'status': 'DONE'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Done Task")

    def test_search_tasks_by_title(self):
        """
        Test searching tasks by title.
        """
        Task.objects.create(user=self.user1, title="Buy Milk")
        Task.objects.create(user=self.user1, title="Walk Dog")

        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.list_url, {'search': 'Milk'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Buy Milk")

    def test_unauthenticated_user_cannot_create_task(self):
        """
        Test unauthenticated user cannot create task.
        """
        self.client.logout()
        data = {"title": "Ghost Task"}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
