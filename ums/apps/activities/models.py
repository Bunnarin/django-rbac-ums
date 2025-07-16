from django.db import models
from django.db.models import Q
from apps.core.json_encoder import CustomJSONEncoder
from apps.core.managers import RLSManager
from apps.core.mixins import TimestampMixin, AuthorMixin, UserRLSMixin
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

class Activity(TimestampMixin, AuthorMixin, FacultyNullMixin, UserRLSMixin):
    """
    Stores user responses to activity templates with row-level security.
    
    Inherits from:
        TimestampMixin: Adds created_at and updated_at fields
        AuthorMixin: Adds author field
        FacultyNullMixin: Adds faculty field that can be null
        UserRLSMixin: Adds row-level security functionality
    
    Attributes:
        template: ForeignKey to ActivityTemplate
        response_json: JSON field storing user responses
    """
    template = models.ForeignKey(ActivityTemplate, null=True, on_delete=models.SET_NULL)
    response_json = models.JSONField(encoder=CustomJSONEncoder, default=dict)

    objects = RLSManager()

    def get_user_rls_filter(self, user):
        """
        Get the row-level security filter for this activity.
        
        Args:
            user: The user to filter by
            
        Returns:
            Q: Django Q object representing the filter
        """
        return Q(author=user)

    def __str__(self): 
        return self.template

    class Meta:
        verbose_name_plural = "Activities"