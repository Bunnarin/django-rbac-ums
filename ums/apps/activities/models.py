from django.db import models
from django.db.models import Q
from django.urls import reverse
from apps.core.managers import RLSManager
from apps.core.mixins import TimestampMixin, AuthorMixin, UserRLSMixin
from apps.organization.mixins import OrganizationMixin

# Create your models here.
class ActivityTemplate(models.Model):
    name = models.CharField(max_length=255, unique=True)
    template_json = models.JSONField()

    def get_absolute_url(self): # this redirect to create a activity with a pk of the template
        return reverse('activities:submit', args=[self.pk])

    def __str__(self): return self.name

class Activity(TimestampMixin, AuthorMixin, OrganizationMixin, UserRLSMixin, models.Model):
    template = models.ForeignKey(ActivityTemplate, null=True, on_delete=models.SET_NULL, related_name='activities')
    response_json = models.JSONField()

    objects = models.Manager()

    secure_objects = RLSManager()

    def get_user_rls_filter(self, user):
        return Q(author=user)

    def __str__(self): return f"{self.template}"