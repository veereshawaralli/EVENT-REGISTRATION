import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from registrations.models import Registration
from registrations.utils import generate_certificate_pdf
from registrations.emails import send_certificate_email
import logging

logging.basicConfig(level=logging.DEBUG)

def test_cert():
    # Find any confirmed registration
    reg = Registration.objects.filter(status='confirmed').first()
    if not reg:
        print("No confirmed registrations found to test.")
        return

    print(f"Testing with Registration ID: {reg.id}")
    try:
        pdf_buffer = generate_certificate_pdf(reg)
        if pdf_buffer:
            print("PDF Buffer generated successfully.")
            print(f"Buffer size: {len(pdf_buffer)} bytes")
            # Try sending email
            try:
                send_certificate_email(reg, pdf_buffer)
                print("Email sent successfully.")
            except Exception as e:
                import traceback
                print("Error sending email:")
                traceback.print_exc()
        else:
            print("Failed to generate PDF buffer. returned None.")
    except Exception as e:
        import traceback
        print("Error generating PDF:")
        traceback.print_exc()

if __name__ == '__main__':
    test_cert()
