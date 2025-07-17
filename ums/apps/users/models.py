from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField
from apps.organization.mixins import OrganizationsNullMixin

class CustomUser(OrganizationsNullMixin, AbstractUser):
    email = models.EmailField("email address", unique=True, blank=True, null=True)
    phone_number = PhoneNumberField(max_length=16, unique=True, blank=True, null=True)

    class UserTypes(models.IntegerChoices):
        STUDENT = 0, 'Student'
        PROFESSOR = 1, 'Professor'
        STAFF = 2, 'Staff'

    user_type = models.IntegerField(choices=UserTypes.choices, default=UserTypes.STAFF)

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        """
        First, make sure that if it's a new user, we set an unusable password
        Second, make sure that we can save multiple users with blank email (because the default can't for some reason)
        """
        if self._state.adding:
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