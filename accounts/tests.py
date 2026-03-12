from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse

from .models import UserProfile


class SignUpViewTests(TestCase):
    """Tests for user registration."""

    def test_signup_page_loads(self):
        response = self.client.get(reverse("accounts:signup"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Sign Up")

    def test_signup_creates_user_and_profile(self):
        data = {
            "username": "testuser",
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        }
        response = self.client.post(reverse("accounts:signup"), data)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(UserProfile.objects.count(), 1)
        self.assertRedirects(response, reverse("events:event_list"))

    def test_duplicate_email_rejected(self):
        User.objects.create_user("existing", "test@example.com", "pass")
        data = {
            "username": "newuser",
            "email": "test@example.com",
            "first_name": "New",
            "last_name": "User",
            "password1": "SecurePass123!",
            "password2": "SecurePass123!",
        }
        response = self.client.post(reverse("accounts:signup"), data)
        self.assertEqual(User.objects.count(), 1)  # Only the first user


class ProfileViewTests(TestCase):
    """Tests for profile page."""

    def setUp(self):
        self.user = User.objects.create_user("testuser", "test@example.com", "testpass123")
        self.client.login(username="testuser", password="testpass123")

    def test_profile_requires_login(self):
        self.client.logout()
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 302)

    def test_profile_page_loads(self):
        response = self.client.get(reverse("accounts:profile"))
        self.assertEqual(response.status_code, 200)
