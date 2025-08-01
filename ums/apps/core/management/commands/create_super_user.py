from django.core.management.base import BaseCommand
from django.db.models import Q
from django.contrib.auth.models import Group
from decouple import config
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    def handle(self, *args, **options):
        existing_admin = User.objects.filter(Q(username=config('SUPERUSER_USERNAME')) | Q(email=config('SUPERUSER_EMAIL'))).first()
        if(existing_admin is None):
            admin_grp, _ = Group.objects.get_or_create(name="ADMIN")
            User.objects.create_superuser(
                username=config('SUPERUSER_USERNAME'),
                email=config('SUPERUSER_EMAIL'),
                groups=[admin_grp]
            )