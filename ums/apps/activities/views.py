from django.views.generic import ListView
from apps.core.views import BaseDeleteView, BaseListView, BaseCreateView, BaseUpdateView
from .models import Activity, ActivityTemplate
from .forms import get_json_form

class ActivityListView(BaseListView):
    """
    View for listing all activities.
    """
    model = Activity
    actions = ["add", "delete"]
    table_fields = ['author', 'template', 'faculty', 'response']

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
        activity_template = ActivityTemplate.objects.get(pk=self.kwargs['template_pk'])
        Form = get_json_form(activity_template.template_definition)
        return super().get_form(form_class=Form)

    def form_valid(self, form):
        form.instance.template = ActivityTemplate.objects.get(pk=self.kwargs['template_pk'])
        form.instance.author = self.request.user
        return super().form_valid(form)

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



