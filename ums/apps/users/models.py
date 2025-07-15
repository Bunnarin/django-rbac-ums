from django.db import models
from django.contrib.auth.models import AbstractUser
from phonenumber_field.modelfields import PhoneNumberField
from apps.organization.mixins import OrganizationsNullMixin

class CustomUser(OrganizationsNullMixin, AbstractUser):
    email = models.EmailField("email address", unique=True, blank=True, null=True,)
    phone_number = PhoneNumberField(max_length=16, unique=True, blank=True, null=True,)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = "User"
        permissions = [
            ("access_global", "Global Access"),
            ("access_faculty_wide", "Faculty Wide Access"),
            ("access_program_wide", "Program Wide Access"),
        ]