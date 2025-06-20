from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

# Create your models here.
class ActivityTemplate(models.Model):
    name = models.CharField(max_length=255, unique=True)
    template_json = models.JSONField()

    def get_absolute_url(self): # this redirect to create a activity with a pk of the template
        return reverse('activities:submit', args=[self.pk])

    def __str__(self): return self.name

class Activity(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    template = models.ForeignKey(ActivityTemplate, null=True, on_delete=models.SET_NULL, related_name='activities')
    author = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='activities')
    response_json = models.JSONField()

    def __str__(self): return f"{self.template}"