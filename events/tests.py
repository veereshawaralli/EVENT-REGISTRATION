from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Event


class EventModelTests(TestCase):
    """Tests for the Event model."""

    def setUp(self):
        self.user = User.objects.create_user("organizer", "org@test.com", "pass123")
        self.event = Event.objects.create(
            title="Test Event",
            description="A test event.",
            date=timezone.now().date() + timezone.timedelta(days=7),
            time=timezone.now().time(),
            location="Test Venue",
            capacity=50,
            organizer=self.user,
        )

    def test_event_str(self):
        self.assertEqual(str(self.event), "Test Event")

    def test_is_upcoming(self):
        self.assertTrue(self.event.is_upcoming)

    def test_seats_remaining(self):
        self.assertEqual(self.event.seats_remaining, 50)

    def test_is_full_false(self):
        self.assertFalse(self.event.is_full)


class EventListViewTests(TestCase):
    """Tests for the event list page."""

    def setUp(self):
        self.user = User.objects.create_user("organizer", "org@test.com", "pass123")
        for i in range(12):
            Event.objects.create(
                title=f"Event {i}",
                description="Test",
                date=timezone.now().date() + timezone.timedelta(days=i + 1),
                time=timezone.now().time(),
                location="Venue",
                capacity=10,
                organizer=self.user,
            )

    def test_event_list_loads(self):
        response = self.client.get(reverse("events:event_list"))
        self.assertEqual(response.status_code, 200)

    def test_pagination(self):
        response = self.client.get(reverse("events:event_list"))
        self.assertTrue(response.context["page_obj"].has_next())

    def test_search(self):
        response = self.client.get(reverse("events:event_list") + "?q=Event+0")
        self.assertEqual(response.status_code, 200)
