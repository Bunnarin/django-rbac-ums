from django.core.management.base import BaseCommand
from django.db.models import Q
from decouple import config
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    def handle(self, *args, **options):
        existing_admin = User.objects.filter(Q(username=config('SUPERUSER_USERNAME')) | Q(email=config('SUPERUSER_EMAIL'))).first()
        if(existing_admin is None):
            User.objects.create_superuser(
                username=config('SUPERUSER_USERNAME'),
                email=config('SUPERUSER_EMAIL'),
                password=config('SUPERUSER_PASSWORD')
            )