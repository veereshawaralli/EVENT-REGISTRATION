import os
import sys

# Add the project directory to the sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_wsgi_application()

# Wrap the application with WhiteNoise and point it to the built static folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
static_root = os.path.join(BASE_DIR, "staticfiles_build")

if not os.path.exists(static_root):
    static_root = os.path.join(BASE_DIR, "staticfiles")

app = WhiteNoise(application, root=static_root)