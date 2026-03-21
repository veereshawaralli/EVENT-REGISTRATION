from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Test SMTP email delivery'

    def add_arguments(self, parser):
        parser.add_argument('email', type=str, help='Recipient email address')

    def handle(self, *args, **options):
        recipient = options['email']
        self.stdout.write(f"Attempting to send a test email to {recipient}...")
        
        try:
            send_mail(
                subject='EventHub SMTP Test',
                message='If you are reading this, your SMTP settings on Render are working perfectly!',
                from_email=None,  # Uses DEFAULT_FROM_EMAIL
                recipient_list=[recipient],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(f"Successfully sent test email to {recipient}!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send email: {e}"))
