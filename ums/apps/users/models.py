from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
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
        if self.is_superuser:
            return super().save(*args, **kwargs)

        creation = not self.pk
        if creation:
            self.set_unusable_password()
        
        # if updating, we need to check if we really need to add to the name
        new_username = self.first_name.lower() + self.last_name.lower()
        if self.username != new_username:
            username_num = CustomUser.objects.filter(username__startswith=new_username).count()
            if username_num > 0:
                self.username = new_username + str(username_num)
            else:
                self.username = new_username
                
        # ensure that staff status always in staff group and if we create a first superuser it thor error for some reason
        
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
    
    def clean(self):
        if self._class and \
            (self._class.faculty != self.faculty or \
                 self._class.program != self.program):
            raise ValidationError("Class must belong to the same faculty and program as the student.")

    def save(self, *args, **kwargs):
        """
        automatically set the affiliation from the class's affiliation
        and, add the affiliation to the user as well
        """
        if self._class:
            self.faculty = self._class.faculty
            self.program = self._class.program
        
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # remove the user if they don't have anymore profile associated (ONLY FOR STUDENT) for clean up purpose
        if self.user.groups.count() == 1 and \
            self.user.user_permissions.count() == 0 and \
            not Student.objects.filter(user=self.user).exclude(pk=self.pk).exists():
            self.user.delete()
        super().delete(*args, **kwargs)