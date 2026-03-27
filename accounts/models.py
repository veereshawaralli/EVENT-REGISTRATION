import uuid
from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    """Extended user profile with optional bio and avatar."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    email_verified = models.BooleanField(default=False)
    verification_token = models.UUIDField(default=uuid.uuid4, editable=False)
    PROVIDER_STATUS_CHOICES = [
        ("none", "Not Applied"),
        ("pending", "Application Pending"),
        ("approved", "Approved"),
        ("active", "Active Organizer"),
        ("rejected", "Rejected"),
    ]

    phone = models.CharField(max_length=20, blank=True)
    is_provider = models.BooleanField(default=False)
    provider_status = models.CharField(
        max_length=20, 
        choices=PROVIDER_STATUS_CHOICES, 
        default="none"
    )
    commission_paid = models.BooleanField(default=False)
    offline_payment_requested = models.BooleanField(default=False)
    company_name = models.CharField(max_length=200, blank=True)
    website = models.URLField(blank=True)
    business_phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username}'s Profile"


class ProviderApplication(UserProfile):
    """Proxy model for provider applications to show in a separate admin section."""
    class Meta:
        proxy = True
        verbose_name = "Provider Application"
        verbose_name_plural = "Provider Applications"
