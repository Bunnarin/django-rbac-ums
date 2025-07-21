from django.db import models
from django.db.models import Q
from django.contrib.auth.models import Group
from django.conf import settings
from apps.organization.mixins import ProgramNullMixin
from apps.core.managers import RLSManager

class ProfileMixin(ProgramNullMixin):
    """
    Abstract base class for models that require a personnel relationship. 
    it requires a faculty and an optional program.
    it also ensure that each profile gets added to the ALL {profile} group
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    objects = RLSManager()

    class Meta:
        abstract = True
        unique_together = ('user', 'faculty', 'program')

    def __str__(self):
        return self.user.__str__()

    def save(self, *args, **kwargs):   
        # put this in here bcuz clean is too early and soemtime we inject the affiliation during form_valid  
        profile_group, _ = Group.objects.get_or_create(name=f"ALL {self.__class__.__name__.upper()}")
        self.user.groups.add(profile_group)
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        profile_group = Group.objects.get(name=f"ALL {self.__class__.__name__.upper()}")
        self.user.groups.remove(profile_group)
        super().delete(*args, **kwargs)

    def get_user_rls_filter(self, user):
        return Q(user=user)