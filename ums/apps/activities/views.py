from django.views.generic import ListView
from apps.core.views import BaseDeleteView, BaseListView, BaseCreateView, BaseUpdateView, BaseBulkDeleteView
from .models import Activity, ActivityTemplate
from apps.core.forms import get_json_form

class ActivityListView(BaseListView):
    """
    View for listing all activities.
    """
    model = Activity
    table_fields = ['author', 'template', 'created_at', 'response', 'faculty']
    object_actions = [('🗑️', 'activities:delete_activity')]
    actions = [('+', 'activities:add_activity'), ('clear all', 'activities:delete_activity')]

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
        self.template = ActivityTemplate.objects.get(pk=self.kwargs['template_pk'])
        template_json = self.template.template_definition
        Form = get_json_form(template_json, Activity, ['response'], 'response')
        return super().get_form(form_class=Form)

    def form_valid(self, form):
        form.instance.template = self.template
        form.instance.author = self.request.user
        return super().form_valid(form)

class ActivityDeleteView(BaseDeleteView):
    model = Activity
    
class ActivityBulkDeleteView(BaseBulkDeleteView):
    model = Activity

class ActivityTemplateListView(BaseListView):
    model = ActivityTemplate
    table_fields = ['name']
    object_actions = [('✏️', 'activities:change_activity_template'), ('🗑️', 'activities:delete_activity_template')]
    actions = [('+', 'activities:add_activity_template')]

class ActivityTemplateCreateView(BaseCreateView):
    model = ActivityTemplate
    
class ActivityTemplateUpdateView(BaseUpdateView):
    model = ActivityTemplate

class ActivityTemplateDeleteView(BaseDeleteView):
    model = ActivityTemplate



