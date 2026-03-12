from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Event(models.Model):
    """An event that users can register for."""

    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=300)
    capacity = models.PositiveIntegerField(help_text="Maximum number of attendees.")
    banner = models.ImageField(
        upload_to="event_banners/",
        blank=True,
        null=True,
        help_text="Event banner image.",
    )
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="organized_events",
    )
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date", "time"]
        verbose_name = "Event"
        verbose_name_plural = "Events"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("events:event_detail", kwargs={"pk": self.pk})

    @property
    def is_upcoming(self):
        """Check if the event hasn't happened yet."""
        return self.date >= timezone.now().date()

    @property
    def registered_count(self):
        """Number of confirmed registrations."""
        return self.registrations.filter(status="confirmed").count()

    @property
    def seats_remaining(self):
        """Number of available seats."""
        return max(0, self.capacity - self.registered_count)

    @property
    def is_full(self):
        """Check if the event has reached capacity."""
        return self.seats_remaining <= 0
