import io
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.conf import settings

def generate_certificate_pdf(registration):
    """
    Generate a PDF certificate for a confirmed registration.
    Returns the raw PDF bytes if successful, else None.
    """
    import os
    from django.conf import settings
    template_path = 'events/certificate_pdf.html'
    
    # Absolute filesystem paths for xhtml2pdf to read images without HTTP requests
    # Must use forward slashes on Windows to prevent CSS escape character errors (\U)
    logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png').replace('\\', '/')
    bg_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'cert_bg.png').replace('\\', '/')
    
    # We pass the registration object so the template can access the user, event, etc.
    context = {
        'registration': registration, 
        'SITE_URL': getattr(settings, 'SITE_URL', 'http://localhost:8000'),
        'LOGO_PATH': logo_path,
        'BG_PATH': bg_path
    }
    
    # Create a Django response object, and specify content_type as pdf
    template = get_template(template_path)
    html = template.render(context)

    # Create a file-like buffer to receive PDF data.
    result = io.BytesIO()

    # Generate PDF
    # pisa.pisaDocument returns an object with an 'err' attribute.
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    
    if not pdf.err:
        return result.getvalue()
    
    return None
