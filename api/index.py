"""REST API using Django REST Framework."""

from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, permissions, serializers

from events.models import Category, Event, Tag
from registrations.models import Registration


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug", "icon")


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class EventListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    organizer = serializers.StringRelatedField()
    is_free = serializers.BooleanField(read_only=True)
    seats_remaining = serializers.IntegerField(read_only=True)
    average_rating = serializers.FloatField(read_only=True)

    class Meta:
        model = Event
        fields = (
            "id", "title", "description", "date", "time", "location",
            "capacity", "seats_remaining", "price", "is_free",
            "banner", "organizer", "category", "tags",
            "is_featured", "average_rating", "created_at",
        )


class RegistrationSerializer(serializers.ModelSerializer):
    event = EventListSerializer(read_only=True)
    event_id = serializers.PrimaryKeyRelatedField(
        queryset=Event.objects.all(), write_only=True, source="event"
    )

    class Meta:
        model = Registration
        fields = ("id", "event", "event_id", "status", "registration_date", "attended")
        read_only_fields = ("status", "registration_date", "attended")

    def validate(self, data):
        request = self.context["request"]
        event = data["event"]
        if event.is_full:
            raise serializers.ValidationError("This event is full. Please join the waitlist.")
        if Registration.objects.filter(user=request.user, event=event, status="confirmed").exists():
            raise serializers.ValidationError("You are already registered for this event.")
        if not event.is_upcoming:
            raise serializers.ValidationError("This event has already taken place.")
        return data

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        validated_data["status"] = "confirmed"
        return super().create(validated_data)


# ---------------------------------------------------------------------------
# Views
# ---------------------------------------------------------------------------

class EventListAPIView(generics.ListAPIView):
    """GET /api/events/ — List upcoming events (public)."""
    serializer_class = EventListSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        qs = Event.objects.filter(date__gte=timezone.now().date()).select_related("category").prefetch_related("tags")
        q = self.request.query_params.get("q", "")
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(location__icontains=q))
        category = self.request.query_params.get("category", "")
        if category:
            qs = qs.filter(category__slug=category)
        return qs


class EventDetailAPIView(generics.RetrieveAPIView):
    """GET /api/events/<pk>/ — Event detail (public)."""
    queryset = Event.objects.all()
    serializer_class = EventListSerializer
    permission_classes = [permissions.AllowAny]


class RegistrationListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /api/registrations/ — My registrations (authenticated)
    POST /api/registrations/ — Register for an event (authenticated)
    """
    serializer_class = RegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Registration.objects.filter(
            user=self.request.user
        ).select_related("event").order_by("-registration_date")


class CategoryListAPIView(generics.ListAPIView):
    """GET /api/categories/ — List all categories."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]