import io
import os

import qrcode
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models

from events.models import Event


class Registration(models.Model):
    """A user's registration for a specific event."""

    STATUS_CHOICES = [
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="registrations",
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="registrations",
    )
    registration_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="confirmed",
    )
    attended = models.BooleanField(default=False)
    qr_code = models.ImageField(upload_to="qr_codes/", blank=True, null=True)

    class Meta:
        # Prevent duplicate active registrations
        constraints = [
            models.UniqueConstraint(
                fields=["user", "event"],
                condition=models.Q(status="confirmed"),
                name="unique_confirmed_registration",
            ),
        ]
        ordering = ["-registration_date"]
        verbose_name = "Registration"
        verbose_name_plural = "Registrations"

    def __str__(self):
        return f"{self.user.username} → {self.event.title} ({self.status})"

    def generate_qr_code(self):
        """Generate and save a QR code image for this registration."""
        from django.urls import reverse
        from django.conf import settings
        
        verify_path = reverse('registrations:verify_ticket', args=[self.pk])
        site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')
        
        # Encode the full verification URL into the QR Code
        data = f"{site_url}{verify_path}"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        filename = f"reg_{self.pk}_qr.png"
        self.qr_code.save(filename, ContentFile(buffer.getvalue()), save=False)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        # Generate QR code only for new confirmed registrations
        if is_new and self.status == "confirmed" and not self.qr_code:
            self.generate_qr_code()
            # Save again with QR code (avoid recursion by calling super directly)
            Registration.objects.filter(pk=self.pk).update(qr_code=self.qr_code)


class Waitlist(models.Model):
    """Users waiting for a spot in a full event."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="waitlist_entries",
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="waitlist",
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "event"],
                name="unique_waitlist_entry",
            )
        ]
        ordering = ["joined_at"]
        verbose_name = "Waitlist Entry"
        verbose_name_plural = "Waitlist Entries"

    def __str__(self):
        return f"{self.user.username} waiting for {self.event.title}"

    @property
    def position(self):
        return Waitlist.objects.filter(
            event=self.event, joined_at__lte=self.joined_at
        ).count()
