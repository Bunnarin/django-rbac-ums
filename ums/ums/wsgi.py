"""
WSGI config for ums project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from decouple import config

# It is critical that DJANGO_SETTINGS_MODULE is set by the environment
# (e.g., your WSGI server like Gunicorn, or your deployment script).
# DO NOT default to 'local' in production.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', config('DJANGO_SETTINGS_MODULE'))

application = get_wsgi_application()
