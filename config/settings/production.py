from .base import *

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25 # Standard SMTP port
EMAIL_USE_TLS = False # Usually no TLS for localhost:25 (unless you configure it)
EMAIL_USE_SSL = False # No SSL either
DEFAULT_FROM_EMAIL = 'portal@rua.edu.kh' # Email address emails will appear to come from
SERVER_EMAIL = DEFAULT_FROM_EMAIL # For error reporting by Django