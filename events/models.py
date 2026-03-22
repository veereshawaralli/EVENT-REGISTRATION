from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify


class Category(models.Model):
    """Event category (e.g. Tech, Music, Workshop)."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    icon = models.CharField(
        max_length=50,
        default="bi-tag",
        help_text="Bootstrap Icon class, e.g. 'bi-laptop'",
    )

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Tag(models.Model):
    """Freeform tag that can be applied to multiple events."""

    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


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

    # New fields
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="events",
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name="events")
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0.00,
        help_text="Ticket price (0 = free).",
    )
    # Optional coordinates for map embed
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

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
    def is_free(self):
        return self.price == 0

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

    @property
    def average_rating(self):
        """Average review rating (1-5), or None if no reviews."""
        reviews = self.reviews.all()
        if not reviews.exists():
            return None
        total = sum(r.rating for r in reviews)
        return round(total / reviews.count(), 1)

    @property
    def waitlist_count(self):
        from registrations.models import Waitlist
        return Waitlist.objects.filter(event=self).count()


class CustomField(models.Model):
    """Custom question for an event registration form."""

    FIELD_TYPES = (
        ("text", "Text Input"),
        ("textarea", "Long Text"),
        ("select", "Dropdown Menu"),
        ("checkbox", "Checkbox"),
    )

    event = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="custom_fields"
    )
    label = models.CharField(max_length=200, help_text="The question to ask.")
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, default="text")
    required = models.BooleanField(default=True)
    placeholder = models.CharField(max_length=200, blank=True, null=True)
    choices = models.TextField(
        blank=True,
        null=True,
        help_text="For Dropdown: Enter options separated by commas.",
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.label} ({self.event.title})"

    def get_choices(self):
        """Convert comma-separated string to list of tuples for Django form."""
        if not self.choices:
            return []
        options = [opt.strip() for opt in self.choices.split(",")]
        return [(opt, opt) for opt in options]
