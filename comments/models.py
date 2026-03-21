from django.conf import settings
from django.db import models

from events.models import Event


class Comment(models.Model):
    """A question or comment posted by any authenticated user on an event."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    body = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Comment"
        verbose_name_plural = "Comments"

    def __str__(self):
        return f"{self.user.username} on '{self.event.title}'"
