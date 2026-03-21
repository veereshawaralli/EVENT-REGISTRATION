"""
Root URL configuration for Event Registration System.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("events/", include("events.urls", namespace="events")),
    path("registrations/", include("registrations.urls", namespace="registrations")),
    path("reviews/", include("reviews.urls", namespace="reviews")),
    path("comments/", include("comments.urls", namespace="comments")),
    path("api/", include("api.urls")),
    # Serve event list directly on root to avoid redirect issues with crawlers
    path("", include("events.urls")), 
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
