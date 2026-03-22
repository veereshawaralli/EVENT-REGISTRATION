from django.contrib import admin

from .models import Category, Event, Tag, CustomField


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
        "registered_count",
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

    def registered_count(self, obj):
        return obj.registered_count

    registered_count.short_description = "Registrations"
