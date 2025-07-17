from django.db import models
# from django.contrib.auth import get_user_model
from django.conf import settings

user = settings.AUTH_USER_MODEL
class StudentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_student=True)

    def create(self, *args, **kwargs):
        kwargs['is_student'] = True
        return super().create(*args, **kwargs)

class ProfessorManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_professor=True)

    def create(self, *args, **kwargs):
        kwargs['is_professor'] = True
        return super().create(*args, **kwargs)

class StaffManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_staff=True)

    def create(self, *args, **kwargs):
        kwargs['is_staff'] = True
        return super().create(*args, **kwargs)