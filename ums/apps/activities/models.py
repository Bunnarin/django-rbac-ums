from django.db import models
from django.db.models import Q
from apps.core.json_encoder import CustomJSONEncoder
from apps.core.managers import RLSManager
from apps.core.mixins import TimestampMixin, AuthorMixin
from apps.organization.mixins import FacultyNullMixin

# Create your models here.
class ActivityTemplate(models.Model):
    """
    Stores JSON-based templates for creating activities.
    
    JSON structure:
        [{
            "label": "the question",
            "type": "text, paragraph, mcq, checkbox, integer, decimal, date",
            "required": "boolean",
            "choices": "if mcq or checkbox, then we populate with a list"
        }]
    
    Attributes:
        name: Unique name for the template
        template_json: JSON field storing the template structure
    """
    name = models.CharField(max_length=255, unique=True)
    template_json = models.JSONField(encoder=CustomJSONEncoder, default=dict)

    def __str__(self): 
        return self.name

class Activity(TimestampMixin, AuthorMixin, FacultyNullMixin):
    """
    Stores user responses to activity templates with row-level security.
    """
    template = models.ForeignKey(ActivityTemplate, null=True, on_delete=models.SET_NULL)
    response_json = models.JSONField(encoder=CustomJSONEncoder, default=dict)

    objects = RLSManager()

    def get_user_rls_filter(self, user):
        return Q(author=user)

    def __str__(self): 
        return f"{self.template.name} activity created by {self.author} on {self.created_at.strftime('%Y-%m-%d')}"

    class Meta:
        verbose_name_plural = "Activities"