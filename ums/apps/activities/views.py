from django.views.generic import ListView, View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import PermissionRequiredMixin
from apps.core.views import BaseExportView, BaseDeleteView, BaseListView, BaseCreateView, BaseUpdateView
from apps.core.forms import generate_dynamic_form_class
from apps.organization.models import Faculty
from .models import Activity, ActivityTemplate
from .forms import translate_json_to_schema, ActivityForm

class ActivityListView(BaseListView):
    """
    View for listing all activities.
    
    Extends BaseListView to provide a filtered list of activities based on user permissions.
    
    Attributes:
        model: The Activity model to display
        actions: List of available actions (add, export, delete)
        table_fields: Fields to display in the activity list
    """
    model = Activity
    actions = ["add", "export", "delete"]
    table_fields = ['author', 'template']
    group_by = ['faculty']

class ActivityTemplateSelectView(ListView):
    """
    View for selecting an activity template.
    """
    model = ActivityTemplate
    template_name = 'core/generic_select.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["redirect_url"] = f'activities:submit_activity'
        return context

class ActivityCreateView(BaseCreateView):
    """
    View for creating new activities 
    """
    model = Activity
    def get_form(self):
        activity_template = get_object_or_404(ActivityTemplate, pk=self.kwargs['template_pk'])
        schema = translate_json_to_schema(activity_template.template_json)
        Form = ActivityForm(schema=schema)
        return Form

    def form_valid(self, form):
        form.instance.template = ActivityTemplate.objects.get(pk=self.kwargs['template_pk'])
        form.instance.author = self.request.user
        return super().form_valid(form)

class ActivityExportView(BaseExportView):
    """
    View for exporting activities to Excel.
    
    Extends BaseExportView to provide Excel export functionality for activities.
    
    Attributes:
        model: The Activity model to export
        fields_to_export: List of fields to include in the export
        json_fields_to_extract: JSON fields to handle separately
    """
    model = Activity
    fields_to_export = [
        ('template', 'Type'),
        ('author', 'Author'),
        ('created_at', 'Created At'),
        ('faculty', 'Faculty'),
        ('response_json', 'Response'),
    ]
    json_fields_to_extract = ['response_json']

class ActivityDeleteView(BaseDeleteView):
    model = Activity

class ActivityTemplateListView(BaseListView):
    model = ActivityTemplate
    actions = ['add', 'change', 'delete']
    table_fields = ['name']

class ActivityTemplateCreateView(BaseCreateView):
    model = ActivityTemplate
    
class ActivityTemplateUpdateView(BaseUpdateView):
    model = ActivityTemplate

class ActivityTemplateDeleteView(BaseDeleteView):
    model = ActivityTemplate



