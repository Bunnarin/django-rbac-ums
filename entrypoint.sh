#!/bin/sh

python manage.py createcachetable
python manage.py migrate --noinput
python manage.py collectstatic --noinput
python manage.py create_super_user
python manage.py crontab add
gunicorn --chdir ums ums.wsgi:application --bind 0.0.0.0:8000
