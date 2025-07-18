#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
from pathlib import Path
from decouple import config

def main():
    """Run administrative tasks."""
    BASE_DIR = Path(__file__).resolve().parent
    CONFIG_DIR = BASE_DIR / 'config'
    PROJECT_DIR = BASE_DIR / 'ums'
    sys.path.insert(0, str(PROJECT_DIR))
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', config('DJANGO_SETTINGS_MODULE', default='config.settings.local'))
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
