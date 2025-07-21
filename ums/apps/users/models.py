from django.db import models
from django.db.models import Q
from django.contrib.auth.models import AbstractUser, Group
from phonenumber_field.modelfields import PhoneNumberField
from apps.organization.mixins import OrganizationsNullMixin
from .mixins import ProfileMixin
from .managers import UserRLSManager

class CustomUser(OrganizationsNullMixin, AbstractUser):
    first_name = models.CharField("first name", max_length=30)
    last_name = models.CharField("last name", max_length=30)
    email = models.EmailField("email address", unique=True, blank=True, null=True)
    phone_number = PhoneNumberField(max_length=16, unique=True, blank=True, null=True)

    objects = UserRLSManager()

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
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

        # if updating, we need to check if we really need to add to the name
        new_username = self.first_name + self.last_name
        if self.username != new_username:
            username_num = CustomUser.objects.filter(username__startswith=new_username).count()
            if username_num > 0:
                self.username = new_username + str(username_num)
            else:
                self.username = new_username
                
        # ensure that staff status always in staff group
        staff_group, _ = Group.objects.get_or_create(name="ALL STAFF")
        if self.is_staff:
            self.groups.add(staff_group)
        elif not creation:
            self.groups.remove(staff_group)

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
    _class = models.ForeignKey(
        'academic.Class', 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='students')
