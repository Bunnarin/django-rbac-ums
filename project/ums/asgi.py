"""
ASGI config for ums project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import sys
from pathlib import Path
from django.core.asgi import get_asgi_application
from decouple import config, Config, RepositoryEnv
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = BASE_DIR / 'config'
sys.path.insert(0, str(BASE_DIR))
config = Config(RepositoryEnv(str(CONFIG_DIR / '.env')))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', config('DJANGO_SETTINGS_MODULE', default='config.settings.local'))
application = get_asgi_application()
