from django.contrib import admin
from django.utils import timezone
from .models import Category, Event, Tag, CustomField, EventCommission


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


class CustomFieldInline(admin.TabularInline):
    model = CustomField
    extra = 1


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Admin interface for Event model."""

    list_display = (
        "title",
        "date",
        "category",
        "price",
        "capacity",
        "registered_count_display",
        "organizer",
        "is_featured",
    )
    list_filter = ("is_featured", "category", "date", "created_at")
    search_fields = ("title", "location", "description")
    filter_horizontal = ("tags",)
    inlines = [CustomFieldInline]
    date_hierarchy = "date"
    list_editable = ("is_featured",)
    readonly_fields = ("created_at", "updated_at")

    def registered_count_display(self, obj):
        return obj.registered_count

    registered_count_display.short_description = "Registrations"


@admin.register(EventCommission)
class EventCommissionAdmin(admin.ModelAdmin):
    list_display = ("event", "get_organizer", "earnings_display", "commission_display", "status", "offline_payment_requested")
    list_filter = ("status", "offline_payment_requested")
    search_fields = ("event__title", "event__organizer__username")
    actions = ["mark_as_paid"]

    def get_organizer(self, obj):
        return obj.event.organizer
    get_organizer.short_description = "Organizer"

    def earnings_display(self, obj):
        return f"₹{obj.earnings}"
    earnings_display.short_description = "Earnings"

    def commission_display(self, obj):
        return f"₹{obj.commission_due}"
    commission_display.short_description = "Due (5%)"

    @admin.action(description="Mark as Paid (Verified)")
    def mark_as_paid(self, request, queryset):
        count = queryset.update(status="paid", paid_at=timezone.now(), offline_payment_requested=False)
        self.message_user(request, f"{count} commissions marked as paid.")
