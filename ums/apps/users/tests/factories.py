# ums/apps/users/factories.py
import factory
from factory import Faker
from factory.django import DjangoModelFactory

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

User = get_user_model()

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('username',)

    username = Faker('user_name')
    
    @factory.post_generation
    def permissions(self, create, extracted, **kwargs):
        if not create:
            return
            
        if extracted:
            # Handle both string codenames and Permission objects
            for perm in extracted:
                if isinstance(perm, str):
                    perm = Permission.objects.get(codename=perm)
                self.user_permissions.add(perm)