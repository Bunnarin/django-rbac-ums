# DEBUG mode, log level, and activation of developer tools like django-debug-toolbar.
from .base import *

DEBUG = True
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

ALLOWED_HOSTS += ['127.0.0.1', 'localhost']