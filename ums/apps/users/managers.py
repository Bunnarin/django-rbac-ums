from django.db import models
# from django.contrib.auth import get_user_model
from django.conf import settings

user = settings.AUTH_USER_MODEL
class StudentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(user_type=user.UserTypes.STUDENT)

    def create(self, *args, **kwargs):
        kwargs['user_type'] = user.UserTypes.STUDENT
        return super().create(*args, **kwargs)

class ProfessorManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(user_type=user.UserTypes.PROFESSOR)

    def create(self, *args, **kwargs):
        kwargs['user_type'] = user.UserTypes.PROFESSOR
        return super().create(*args, **kwargs)

class StaffManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(user_type=user.UserTypes.STAFF)

    def create(self, *args, **kwargs):
        kwargs['user_type'] = user.UserTypes.STAFF
        return super().create(*args, **kwargs)