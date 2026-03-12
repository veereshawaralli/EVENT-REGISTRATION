from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Admin interface for Event model."""

    list_display = (
        "title",
        "date",
        "time",
        "location",
        "capacity",
        "registered_count",
        "organizer",
        "is_featured",
    )
    list_filter = ("is_featured", "date", "created_at")
    search_fields = ("title", "location", "description")
    date_hierarchy = "date"
    list_editable = ("is_featured",)
    readonly_fields = ("created_at", "updated_at")

    def registered_count(self, obj):
        return obj.registered_count

    registered_count.short_description = "Registrations"
