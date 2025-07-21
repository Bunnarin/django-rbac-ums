from django.db import models
from django.db.models import Q
from django.conf import settings
from django_jsonform.models.fields import JSONField
from apps.core.json_encoder import CustomJSONEncoder
from apps.core.managers import RLSManager
from apps.organization.mixins import FacultyNullMixin

# Create your models here.
class ActivityTemplate(models.Model):
    """
    Stores JSON-based templates for creating activities.
    
    Attributes:
        name: Unique name for the template
        template_json: JSON field storing the template structure
    """
    TEMPLATE_SCHEMA = {
        "type": "array",
        "items": {
            "type": "object",
            "keys": {
                "title": {"type": "string"},
                "type": {"type": "string",
                        "choices": [
                            "text",
                            "paragraph",
                            "integer",
                            "number",
                            "date",
                            "date-time",
                            "time",
                            "dropdown",
                            "checkbox"
                        ]},
                "required": {"type": "boolean"},
                "choices": {"type": "array", "items": {"type": "string"}}
            }
        }
    }
    
    name = models.CharField(max_length=255, unique=True)
    template_json = JSONField(schema=TEMPLATE_SCHEMA, encoder=CustomJSONEncoder)

    def __str__(self): 
        return self.name

class Activity(FacultyNullMixin):
    """
    Stores user responses to activity templates with row-level security.
    """
    template = models.ForeignKey(ActivityTemplate, null=True, on_delete=models.SET_NULL)
    response_json = models.JSONField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Last Updated At")

    objects = RLSManager()

    def get_user_rls_filter(self, user):
        return Q(author=user)

    def __str__(self): 
        return f"{self.template.name if self.template else ''} activity created by {self.author} on {self.created_at.strftime('%Y-%m-%d')}"

    class Meta:
        verbose_name_plural = "Activities"