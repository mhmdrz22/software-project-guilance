from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()

class AuthIntegrationTests(APITestCase):
    def setUp(self):
        self.register_url = reverse("register")
        self.login_url = reverse("token_obtain_pair")
        self.me_url = reverse("me")

        # Pre-create a user for login tests
        self.existing_user = User.objects.create_user(
            email="existing@example.com",
            password="strongpassword123",
            username="existinguser"
        )

    def test_register_user_happy_path(self):
        """
        Ensure a new user can register successfully.
        """
        data = {
            "email": "newuser@example.com",
            "password": "newpassword123",
            "username": "newuser"
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)  # Existing + New
        self.assertEqual(User.objects.get(email="newuser@example.com").username, "newuser")

    def test_register_duplicate_email_sad_path(self):
        """
        Ensure duplicate email registration fails.
        """
        data = {
            "email": "existing@example.com",
            "password": "password123"
        }
        response = self.client.post(self.register_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_happy_path(self):
        """
        Ensure user can obtain JWT tokens with correct credentials.
        """
        data = {
            "email": "existing@example.com",
            "password": "strongpassword123"
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_invalid_password_sad_path(self):
        """
        Ensure login fails with wrong password.
        """
        data = {
            "email": "existing@example.com",
            "password": "wrongpassword"
        }
        response = self.client.post(self.login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_me_authenticated(self):
        """
        Ensure authenticated user can fetch their own profile.
        """
        self.client.force_authenticate(user=self.existing_user)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "existing@example.com")

    def test_get_me_unauthenticated(self):
        """
        Ensure unauthenticated user cannot access profile endpoint.
        """
        self.client.logout()  # Ensure no auth
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
