# DEBUG mode, log level, and activation of developer tools like django-debug-toolbar.
from .base import *
import dj_database_url
from decouple import config

DATABASES = {
    'default': dj_database_url.parse(config('DATABASE_URL'))
}

DEBUG = True
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

INSTALLED_APPS += ['debug_toolbar', ]