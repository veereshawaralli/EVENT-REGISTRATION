from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse

def _get_site_url():
    return getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')

def send_html_email(subject, template_name, context, recipient_list):
    """
    Helper to send a multi-part HTML email.
    """
    # Ensure site_url and dashboard_url are always in context
    site_url = _get_site_url()
    context['site_url'] = site_url
    context['dashboard_url'] = f"{site_url}{reverse('registrations:dashboard')}"
    
    html_content = render_to_string(template_name, context)
    text_content = strip_tags(html_content)
    
    email = EmailMultiAlternatives(
        subject=subject,
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=recipient_list
    )
    email.attach_alternative(html_content, "text/html")
    return email.send(fail_silently=True)

def send_registration_confirmation(registration):
    """
    Send a rich confirmation email with a QR code ticket.
    """
    event = registration.event
    user = registration.user
    site_url = _get_site_url()
    
    qr_code_url = ""
    if registration.qr_code:
        qr_code_url = f"{site_url}{registration.qr_code.url}"
    
    context = {
        'user': user,
        'event': event,
        'registration': registration,
        'qr_code_url': qr_code_url,
    }
    
    subject = f"✅ Confirmed: Your spot for {event.title}"
    return send_html_email(subject, 'emails/registration_confirmation.html', context, [user.email])

def send_waitlist_promotion(user, event):
    """
    Notify a waitlisted user that a spot has opened up.
    """
    context = {
        'user': user,
        'event': event,
    }
    subject = f"🎉 Good News! A spot opened for {event.title}"
    return send_html_email(subject, 'emails/waitlist_promotion.html', context, [user.email])

def send_event_reminder(registration):
    """
    Send a reminder email 24 hours before the event.
    """
    event = registration.event
    user = registration.user
    site_url = _get_site_url()
    
    qr_code_url = ""
    if registration.qr_code:
        qr_code_url = f"{site_url}{registration.qr_code.url}"
    
    context = {
        'user': user,
        'event': event,
        'registration': registration,
        'qr_code_url': qr_code_url,
    }
    
    subject = f"⏰ Reminder: {event.title} is tomorrow!"
    return send_html_email(subject, 'emails/event_reminder.html', context, [user.email])
