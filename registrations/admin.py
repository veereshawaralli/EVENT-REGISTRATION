from django.contrib import admin

from .models import Registration


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    """Admin interface for Registration model."""

    list_display = ("user", "event", "registration_date", "status")
    list_filter = ("status", "registration_date")
    search_fields = ("user__username", "user__email", "event__title")
    list_editable = ("status",)
    raw_id_fields = ("user", "event")
