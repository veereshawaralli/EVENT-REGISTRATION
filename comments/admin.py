from django.contrib import admin

from .models import Comment


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "created_at")
    list_filter = ("event",)
    search_fields = ("user__username", "event__title", "body")
    readonly_fields = ("created_at",)
