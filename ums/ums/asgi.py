"""
ASGI config for ums project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

# It is critical that DJANGO_SETTINGS_MODULE is set by the environment
# (e.g., your ASGI server like Uvicorn, or your deployment script).
# DO NOT default to 'local' in production.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

application = get_asgi_application()
