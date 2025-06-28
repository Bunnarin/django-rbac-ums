from django import forms
from .models import ActivityTemplate

class ActivityTemplateForm(forms.ModelForm):
    class Meta:
        model = ActivityTemplate
        fields = ['name']