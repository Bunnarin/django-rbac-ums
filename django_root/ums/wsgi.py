"""
WSGI config for ums project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys
from pathlib import Path

current_dir = Path(__file__).resolve().parent
django_root_dir = current_dir / 'django_root'
sys.path.insert(0, str(django_root_dir))
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

application = get_wsgi_application()
