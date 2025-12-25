from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

class AccountAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123",
            "password2": "password123",
        }
        self.login_data = {
            "email": "newuser@example.com",
            "password": "password123",
        }

    def test_user_registration(self):
        """Test that a new user can register."""
        response = self.client.post("/api/auth/register/", self.register_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email=self.register_data["email"]).exists())

    def test_user_login_and_get_token(self):
        """Test that a registered user can log in and get a JWT token."""
        # First, register the user
        self.client.post("/api/auth/register/", self.register_data)

        # Then, try to log in
        response = self.client.post("/api/auth/token/", self.login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_get_current_user_info(self):
        """Test that an authenticated user can retrieve their own info."""
        # Register and log in to get the token
        self.client.post("/api/auth/register/", self.register_data)
        login_response = self.client.post("/api/auth/token/", self.login_data)
        token = login_response.data["access"]

        # Use the token to authenticate
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.get("/api/auth/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.register_data["email"])
        self.assertEqual(response.data["username"], self.register_data["username"])
