from django.db import models
from django.db.models import Q
from django.contrib.auth.models import Group
from django.conf import settings
from django.core.exceptions import ValidationError
from apps.organization.mixins import ProgramNullMixin
from .managers import UserRLSManager

class ProfileMixin(ProgramNullMixin):
    """
    Abstract base class for models that require a personnel relationship. 
    it requires a faculty and an optional program.
    it also ensure that each profile gets added to the ALL {profile} group
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    objects = UserRLSManager()

    class Meta:
        abstract = True

    def __str__(self):
        return self.user.username

    def clean(self):
        """
        ensure that the user doesn't have a profile for this faculty and program
        """
        super().clean()        
        if self.__class__.objects.filter(user=self.user, faculty=self.faculty, program=self.program).exists():
            raise ValidationError("This user already has a profile for this faculty and program.")

    def save(self, *args, **kwargs):        
        profile_group, _ = Group.objects.get_or_create(name=f"ALL {self.__class__.__name__}")
        self.user.groups.add(profile_group)
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        profile_group = Group.objects.get(name=f"ALL {self.__class__.__name__}")
        self.user.groups.remove(profile_group)
        super().delete(*args, **kwargs)

    def get_user_rls_filter(self, user):
        return Q(user=user)