from django.contrib.auth.models import UserManager
from apps.core.managers import RLSManager

class UserRLSManager(RLSManager, UserManager):
    pass