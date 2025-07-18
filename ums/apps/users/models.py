from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField
from apps.organization.mixins import OrganizationsNullMixin, ProgramNullMixin
from .mixins import ProfileMixin
from .managers import UserRLSManager

class CustomUser(OrganizationsNullMixin, AbstractUser):
    email = models.EmailField("email address", unique=True, blank=True, null=True)
    phone_number = PhoneNumberField(max_length=16, unique=True, blank=True, null=True)

    objects = UserRLSManager()

    def __str__(self):
        return self.username
    
    def get_user_rls_filter(self, user):
        return Q(username=user.username)

    def save(self, *args, **kwargs):
        """
        First, make sure that if it's a new user, we set an unusable password
        Second, make sure that we can save multiple users with blank email (because the default can't for some reason)
        """
        creation = not self.pk
        if creation:
            self.set_unusable_password()

        if self.email == '':
            self.email = None

        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "User"
        permissions = [
            ("access_global", "Global Access"),
            ("access_faculty_wide", "Faculty Wide Access"),
            ("access_program_wide", "Program Wide Access"),
        ]

class Professor(ProfileMixin):
    pass

class Student(ProfileMixin):
    pass

class Staff(ProfileMixin):
    pass
    
