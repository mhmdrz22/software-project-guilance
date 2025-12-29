from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .serializers import RegisterSerializer

User = get_user_model()

class UserManagerTests(TestCase):
    def test_create_user_email_normalization(self):
        """
        Test that email is normalized to lowercase.
        """
        email = "TEST@Example.com"
        user = User.objects.create_user(email=email, password="password123")
        self.assertEqual(user.email, "test@example.com")

    def test_create_user_raises_error_without_email(self):
        """
        Test that creating a user without an email raises ValueError.
        """
        with self.assertRaises(ValueError):
            User.objects.create_user(email=None, password="password123")

    def test_create_superuser_flags(self):
        """
        Test that create_superuser sets correct flags.
        """
        admin = User.objects.create_superuser(email="admin@example.com", password="password123")
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_active)

    def test_password_hashing(self):
        """
        Test that password is hashed, not stored in plain text.
        """
        user = User.objects.create_user(email="secure@example.com", password="secretpassword")
        self.assertNotEqual(user.password, "secretpassword")
        self.assertTrue(user.check_password("secretpassword"))

class RegisterSerializerTests(TestCase):
    def setUp(self):
        self.user_data = {
            "email": "unique@example.com",
            "password": "strongpassword123",
            "username": "uniqueuser"
        }

    def test_duplicate_email_validation_case_insensitive(self):
        """
        Test that serializer rejects email if it exists (case-insensitive).
        """
        User.objects.create_user(email="unique@example.com", password="oldpassword")

        # Try to register with same email but different casing
        data = {
            "email": "UNIQUE@example.com",
            "password": "newpassword123",
            "username": "newuser"
        }
        serializer = RegisterSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("email", serializer.errors)
        self.assertEqual(str(serializer.errors["email"][0]), "A user with that email already exists.")

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
