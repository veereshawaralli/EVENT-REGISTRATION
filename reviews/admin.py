from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "rating", "created_at")
    list_filter = ("rating", "event")
    search_fields = ("user__username", "event__title", "comment")
    readonly_fields = ("created_at",)
