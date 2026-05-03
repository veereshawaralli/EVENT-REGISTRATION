from django.urls import path

from . import views

app_name = "events"

urlpatterns = [
    path("", views.event_list, name="event_list"),
    path("<int:pk>/", views.event_detail, name="event_detail"),
    path("create/", views.EventCreateView.as_view(), name="event_create"),
    path("<int:pk>/edit/", views.EventUpdateView.as_view(), name="event_update"),
    path("<int:pk>/delete/", views.EventDeleteView.as_view(), name="event_delete"),
    path("dashboard/", views.organizer_dashboard, name="organizer_dashboard"),
    path("<int:event_id>/export-attendees/", views.export_attendees_csv, name="export_attendees_csv"),
    path("scanner/", views.qr_scanner, name="qr_scanner"),

    # Commission Payments
    path("commission/<int:event_id>/checkout/", views.event_commission_checkout, name="commission_checkout"),
    path("commission/<int:event_id>/callback/", views.event_commission_callback, name="commission_callback"),
    path("commission/<int:event_id>/offline/", views.event_commission_offline, name="commission_offline"),
    
    # Policy Pages
    path("about/", views.about_us, name="about"),
    path("contact/", views.contact_us, name="contact"),
    path("privacy/", views.privacy_policy, name="privacy"),
    path("terms/", views.terms_conditions, name="terms"),
    path("refund/", views.refund_policy, name="refund"),
    path("api/ai-generate/", views.ai_generate_event_content, name="ai_generate"),
    
    # Certificate Builder
    path("<int:event_id>/certificate-builder/", views.certificate_builder, name="certificate_builder"),
    path("<int:event_id>/certificate-preview/", views.certificate_preview, name="certificate_preview"),
    path("<int:event_id>/certificate-preview/pdf/", views.certificate_preview_pdf, name="certificate_preview_pdf"),
    path("certificate/<int:registration_id>/send/", views.send_certificate_manual, name="send_certificate_manual"),
]
