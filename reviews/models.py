from django.conf import settings
from django.db import models

from events.models import Event


class Review(models.Model):
    """Star rating + comment left by a verified attendee after an event."""

    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField(max_length=1000, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # One review per user per event
        constraints = [
            models.UniqueConstraint(fields=["user", "event"], name="unique_user_event_review"),
        ]
        ordering = ["-created_at"]
        verbose_name = "Review"
        verbose_name_plural = "Reviews"

    def __str__(self):
        return f"{self.user.username} → {self.event.title}: {self.rating}★"

    @property
    def star_range(self):
        return range(1, 6)
