from django.urls import path

from . import views

app_name = "registrations"

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("register/<int:event_id>/", views.register_for_event, name="register"),
    path("cancel/<int:registration_id>/", views.cancel_registration, name="cancel"),
    path("waitlist/join/<int:event_id>/", views.join_waitlist, name="join_waitlist"),
    path("waitlist/leave/<int:event_id>/", views.leave_waitlist, name="leave_waitlist"),
    path("ics/<int:registration_id>/", views.download_ics, name="download_ics"),
    path("checkout/<int:registration_id>/", views.payment_checkout, name="checkout"),
    path("payment-callback/", views.payment_callback, name="payment_callback"),
    path("verify/<int:registration_id>/", views.verify_ticket, name="verify_ticket"),
    path("attend/<int:registration_id>/", views.mark_attended, name="mark_attended"),
]
