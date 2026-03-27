from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.urls import reverse

from registrations.emails import send_html_email

def _get_site_url():
    return getattr(settings, 'SITE_URL', 'http://localhost:8000').rstrip('/')

def send_verification_email(user):
    """
    Send an email verification link to a new user.
    """
    site_url = _get_site_url()
    token = user.profile.verification_token
    verify_url = f"{site_url}{reverse('accounts:verify_email', args=[token])}"
    
    context = {
        'user': user,
        'verify_url': verify_url,
    }
    
    return send_html_email(
        "Verify your EventHub account",
        'emails/email_verification.html',
        context,
        [user.email]
    )
