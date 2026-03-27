from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse

from .models import UserProfile, ProviderApplication


class UserProfileInline(admin.StackedInline):
    """Inline profile editor on the User admin page."""

    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"


class UserAdmin(BaseUserAdmin):
    """Extended User admin with inline profile and provider management."""

    inlines = (UserProfileInline,)
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "get_provider_status", "get_offline_request")
    list_filter = ("is_staff", "is_superuser", "is_active", "profile__provider_status", "profile__offline_payment_requested")
    actions = ["approve_providers", "reject_providers", "activate_providers_manual"]

    @admin.display(description="Provider Status")
    def get_provider_status(self, obj):
        return obj.profile.get_provider_status_display()

    @admin.display(description="Offline Req?", boolean=True)
    def get_offline_request(self, obj):
        return obj.profile.offline_payment_requested

    @admin.action(description="Approve selected provider applications")
    def approve_providers(self, request, queryset):
        profiles = UserProfile.objects.filter(user__in=queryset)
        count = profiles.update(provider_status="active", is_provider=True)
        self.message_user(request, f"{count} provider applications approved and activated.")

    @admin.action(description="Reject selected provider applications")
    def reject_providers(self, request, queryset):
        profiles = UserProfile.objects.filter(user__in=queryset)
        count = profiles.update(provider_status="rejected", is_provider=False)
        self.message_user(request, f"{count} provider applications rejected.")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Dedicated admin for managing provider profiles and applications."""
    list_display = ("user", "company_name", "provider_status", "is_provider", "created_at")
    list_filter = ("provider_status", "is_provider")
    search_fields = ("user__username", "company_name", "user__email")
    actions = ["approve_app", "reject_app"]

    @admin.action(description="Approve Application & Activate")
    def approve_app(self, request, queryset):
        count = queryset.update(provider_status="active", is_provider=True)
        self.message_user(request, f"{count} applications approved and activated.")

    @admin.action(description="Reject Application")
    def reject_app(self, request, queryset):
        count = queryset.update(provider_status="rejected", is_provider=False)
        self.message_user(request, f"{count} applications rejected.")


@admin.register(ProviderApplication)
class ProviderApplicationAdmin(admin.ModelAdmin):
    """Dedicated section for approving new provider applications."""
    list_display = ("user", "company_name", "website", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "company_name", "user__email")
    actions = ["approve_app", "reject_app"]

    def get_queryset(self, request):
        """Show only pending applications."""
        return super().get_queryset(request).filter(provider_status="pending")

    @admin.action(description="✅ Approve & Activate Selection")
    def approve_app(self, request, queryset):
        count = queryset.update(provider_status="active", is_provider=True)
        self.message_user(request, f"{count} applications approved and activated.")

    @admin.action(description="❌ Reject Selection")
    def reject_app(self, request, queryset):
        count = queryset.update(provider_status="rejected", is_provider=False)
        self.message_user(request, f"{count} applications rejected.")


# Re-register User with extended admin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
