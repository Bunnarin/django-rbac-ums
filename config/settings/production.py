from .base import *

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25 # Standard SMTP port
EMAIL_USE_TLS = False # Usually no TLS for localhost:25 (unless you configure it)
EMAIL_USE_SSL = False # No SSL either
DEFAULT_FROM_EMAIL = 'portal@rua.edu.kh' # Email address emails will appear to come from
SERVER_EMAIL = DEFAULT_FROM_EMAIL # For error reporting by Django
ALLOWED_HOSTS = ['camfood.in']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ums_db',
        'USER': 'ums_user',
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': 'postgresql',
        'PORT': '5432',
    }
}

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_CONTENT_TYPE_NOSNIFF = True