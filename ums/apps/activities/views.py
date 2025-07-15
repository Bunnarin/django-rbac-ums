from django.views.generic import ListView, View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import PermissionRequiredMixin
from apps.core.views import BaseExportView, BaseTemplateBuilderView, BaseDeleteView, BaseListView
from apps.core.forms import generate_dynamic_form_class
from .models import Activity, ActivityTemplate
# Create your views here.
class ActivityListView(BaseListView):
    model = Activity
    actions = ["add", "export", "delete"]
    table_fields = ['author', 'faculty', 'template']

class ActivityTemplateSelectView(ListView):
    model = ActivityTemplate
    template_name = 'core/generic_select.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["redirect_url"] = f'activities:submit_activity'
        return context

class ActivityCreateView(PermissionRequiredMixin, View):
    model = Activity
    template_name = 'core/generic_form.html'

    def get_permission_required(self):
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name.lower()
        return [f'{self.app_label}.add_{self.model_name}']

    def get(self, request, template_pk):
        activity_template = get_object_or_404(ActivityTemplate, pk=template_pk)
        template_json = activity_template.template_json
        Form = generate_dynamic_form_class(template_json)
        form = Form()
        return render(request, self.template_name, {'form': form})

    def post(self, request, template_pk):
        activity_template = get_object_or_404(ActivityTemplate, pk=template_pk)
        template_json = activity_template.template_json
        Form = generate_dynamic_form_class(template_json)
        form = Form(request.POST)

        if form.is_valid():
            Activity.objects.create(
                template = activity_template,
                author = request.user,
                faculty = request.user.faculty,
                response_json = form.cleaned_data,
            )
            return redirect(f'{self.app_label}:view_{self.model_name}')
        else:
            return render(request, self.template_name, {'form': form})

class ActivityExportView(BaseExportView):
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

class ActivityTemplateCreateView(BaseTemplateBuilderView):
    model = ActivityTemplate
    default_form_fields = ['name']
    json_field_name_in_model = 'template_json'

class ActivityTemplateListView(BaseListView):
    model = ActivityTemplate
    actions = ["add", "delete"]
    table_fields = ['name']

class ActivityTemplateDeleteView(BaseDeleteView):
    model = ActivityTemplate
