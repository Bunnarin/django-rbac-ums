from django.db import models
from django.db.models import Q
from django.urls import reverse
from apps.core.json_encoder import CustomJSONEncoder
from apps.core.managers import RLSManager
from apps.core.mixins import TimestampMixin, AuthorMixin, UserRLSMixin
from apps.organization.mixins import FacultyNullMixin

# Create your models here.
class ActivityTemplate(models.Model):
    name = models.CharField(max_length=255, unique=True)
    template_json = models.JSONField(encoder=CustomJSONEncoder, default=dict)

    def __str__(self): return self.name

class Activity(TimestampMixin, AuthorMixin, FacultyNullMixin, UserRLSMixin):
    template = models.ForeignKey(ActivityTemplate, null=True, on_delete=models.SET_NULL)
    response_json = models.JSONField(encoder=CustomJSONEncoder, default=dict)

    objects = RLSManager()

    def get_user_rls_filter(self, user):
        return Q(author=user)

    def __str__(self): return f"{self.template}"

    class Meta:
        verbose_name_plural = "Activities"