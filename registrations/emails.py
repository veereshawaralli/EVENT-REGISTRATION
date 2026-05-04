from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse
from email.mime.image import MIMEImage
import os

def _get_site_url():
    return getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')

def _attach_logo(email):
    """Helper to attach the project logo as CID:logo."""
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
    if os.path.exists(logo_path):
        try:
            with open(logo_path, 'rb') as f:
                logo_content = f.read()
            mime_logo = MIMEImage(logo_content)
            mime_logo.add_header('Content-ID', '<logo>')
            mime_logo.add_header('Content-Disposition', 'inline', filename='logo.png')
            email.attach(mime_logo)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Failed to attach logo CID: {e}")

def send_html_email(subject, template_name, context, recipient_list, inline_images=None):
    """
    Helper to send a multi-part HTML email with optional inline images (CIDs).
    Automatically attaches the project logo as 'logo' CID.
    """
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
    
    # 1. Automatically attach the logo as CID:logo
    _attach_logo(email)

    # 2. Attach additional inline images if provided
    if inline_images:
        for cid, img_file in inline_images.items():
            try:
                # Ensure we have binary content (handles both local and remote storage)
                if hasattr(img_file, 'open'):
                    img_file.open('rb')
                    content = img_file.read()
                    img_file.close()
                else:
                    img_file.seek(0)
                    content = img_file.read()
                
                mime_image = MIMEImage(content)
                mime_image.add_header('Content-ID', f'<{cid}>')
                mime_image.add_header('Content-Disposition', 'inline', filename=cid)
                email.attach(mime_image)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to attach inline image {cid}: {e}")
                
    return email.send(fail_silently=False)

def send_registration_confirmation(registration):
    """
    Send a rich confirmation email with an embedded QR code ticket.
    """
    event = registration.event
    user = registration.user
    
    inline_images = {}
    if registration.qr_code:
        inline_images['qrcode'] = registration.qr_code
            
    context = {
        'user': user,
        'event': event,
        'registration': registration,
        'include_qr': bool(registration.qr_code),
    }
    
    subject = f"✅ Confirmed: Your spot for {event.title}"
    return send_html_email(
        subject, 
        'emails/registration_confirmation.html', 
        context, 
        [user.email],
        inline_images=inline_images
    )

def send_registration_cancellation(user, event):
    """
    Notify a user that their registration has been cancelled.
    """
    context = {
        'user': user,
        'event': event,
    }
    subject = f"❌ Cancelled: {event.title}"
    return send_html_email(subject, 'emails/registration_cancellation.html', context, [user.email])

def send_waitlist_notification(user, event):
    """
    Notify a user that they've been added to the waitlist.
    """
    context = {
        'user': user,
        'event': event,
    }
    subject = f"⏳ Waitlisted: {event.title}"
    return send_html_email(subject, 'emails/waitlist_notification.html', context, [user.email])

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
    Send a reminder email 24 hours before the event with embedded QR code.
    """
    event = registration.event
    user = registration.user
    
    inline_images = {}
    if registration.qr_code:
        inline_images['qrcode'] = registration.qr_code
            
    context = {
        'user': user,
        'event': event,
        'registration': registration,
        'include_qr': bool(registration.qr_code),
    }
    
    subject = f"⏰ Reminder: {event.title} is tomorrow!"
    return send_html_email(
        subject, 
        'emails/event_reminder.html', 
        context, 
        [user.email],
        inline_images=inline_images
    )

def send_certificate_email(registration, pdf_buffer):
    """
    Send the user their certificate of participation after checking in.
    """
    event = registration.event
    user = registration.user
    
    site_url = _get_site_url()
    context = {
        'user': user,
        'event': event,
        'site_url': site_url,
        'dashboard_url': f"{site_url}{reverse('registrations:dashboard')}"
    }
    
    html_content = render_to_string('emails/certificate_email.html', context)
    text_content = strip_tags(html_content)
    
    email = EmailMultiAlternatives(
        subject=f"🎓 Your Certificate for {event.title}",
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email]
    )
    email.attach_alternative(html_content, "text/html")
    
    # Attach logo for cid:logo reference in template
    _attach_logo(email)
    
    if pdf_buffer:
        email.attach(f"Certificate_{event.title.replace(' ', '_')}.pdf", pdf_buffer, 'application/pdf')
        
    return email.send(fail_silently=False)
