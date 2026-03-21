from django.contrib import admin

from .models import Registration, Waitlist


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "status", "attended", "registration_date")
    list_filter = ("status", "attended", "event")
    search_fields = ("user__username", "event__title")
    list_editable = ("attended",)
    readonly_fields = ("registration_date", "qr_code")
    actions = ["mark_attended", "mark_not_attended"]

    @admin.action(description="Mark selected as attended")
    def mark_attended(self, request, queryset):
        queryset.update(attended=True)

    @admin.action(description="Mark selected as not attended")
    def mark_not_attended(self, request, queryset):
        queryset.update(attended=False)


@admin.register(Waitlist)
class WaitlistAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "position", "joined_at")
    list_filter = ("event",)
    search_fields = ("user__username", "event__title")
    readonly_fields = ("joined_at",)
