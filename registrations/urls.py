from django.urls import path

from . import views

app_name = "registrations"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("register/<int:event_id>/", views.register_for_event, name="register"),
    path("cancel/<int:registration_id>/", views.cancel_registration, name="cancel"),
]
