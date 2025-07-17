# DEBUG mode, log level, and activation of developer tools like django-debug-toolbar.
from .base import *
from decouple import config

DEBUG = True
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ums_db',
        'USER': 'ums_user',
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': '5432',
    }
}