from django.db import models
from django.contrib.auth.models import User
from apps.organization.mixins import OrganizationMixin

# Create your models here.
class Profile(OrganizationMixin, models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username

    class Meta:
        permissions = [
            ("access_program_wide", "program-wide access"),
            ("access_faculty_wide", "faculty-wide access"),
            ("access_global", "university-wide access"),
        ]