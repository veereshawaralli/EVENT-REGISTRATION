from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from events.models import Event

from .models import Registration


class RegistrationTests(TestCase):
    """Tests for the registration workflow."""

    def setUp(self):
        self.organizer = User.objects.create_user("organizer", "org@test.com", "pass123")
        self.user = User.objects.create_user("attendee", "att@test.com", "pass123")
        self.event = Event.objects.create(
            title="Test Conference",
            description="A test event.",
            date=timezone.now().date() + timezone.timedelta(days=7),
            time=timezone.now().time(),
            location="Test Venue",
            capacity=2,
            organizer=self.organizer,
        )
        self.client.login(username="attendee", password="pass123")

    def test_register_for_event(self):
        url = reverse("registrations:register", args=[self.event.pk])
        response = self.client.post(url)
        self.assertEqual(Registration.objects.filter(status="confirmed").count(), 1)
        self.assertRedirects(response, reverse("events:event_detail", args=[self.event.pk]))

    def test_prevent_duplicate_registration(self):
        Registration.objects.create(user=self.user, event=self.event, status="confirmed")
        url = reverse("registrations:register", args=[self.event.pk])
        self.client.post(url)
        self.assertEqual(
            Registration.objects.filter(user=self.user, event=self.event, status="confirmed").count(),
            1,
        )

    def test_capacity_respected(self):
        user2 = User.objects.create_user("user2", "u2@test.com", "pass123")
        user3 = User.objects.create_user("user3", "u3@test.com", "pass123")
        Registration.objects.create(user=self.user, event=self.event, status="confirmed")
        Registration.objects.create(user=user2, event=self.event, status="confirmed")
        # Third user should be rejected (capacity=2)
        self.client.login(username="user3", password="pass123")
        url = reverse("registrations:register", args=[self.event.pk])
        self.client.post(url)
        self.assertEqual(
            Registration.objects.filter(event=self.event, status="confirmed").count(),
            2,
        )

    def test_cancel_registration(self):
        reg = Registration.objects.create(user=self.user, event=self.event, status="confirmed")
        url = reverse("registrations:cancel", args=[reg.pk])
        self.client.post(url)
        reg.refresh_from_db()
        self.assertEqual(reg.status, "cancelled")

    def test_dashboard_loads(self):
        response = self.client.get(reverse("registrations:dashboard"))
        self.assertEqual(response.status_code, 200)
