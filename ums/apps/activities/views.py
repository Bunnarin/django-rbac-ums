from django.views.generic import ListView, View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import PermissionRequiredMixin
from apps.core.views import BaseExportView
from apps.core.forms import generate_dynamic_form_class
from apps.core.mixins.views import ListViewPermissionMixin, CreateViewPermissionMixin
from .models import Activity, ActivityTemplate
# Create your views here.
class ActivityListView(ListViewPermissionMixin, ListView):
    model = Activity
    template_name = 'core/generic_list.html' # Use the generic template

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Define the fields to display in the table
        context['table_headers'] = [
            'Author', 'Faculty', 'Program', 'Type'
        ]
        context['table_fields'] = [
            'author', 'faculty', 'program', 'template'
        ]

        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name.lower()

        # check permission
        user = self.request.user
        actions = ["add", "change", "delete", "view"]
        for action in actions:
            permission = f'{app_label}.{action}_{model_name}'
            if user.has_perm(permission):
                url = permission.replace('.', ':')
                context[f"{action}_url"] = url

        context['export_url'] = f'{app_label}:export_{model_name}'
        return context

class ActivityTemplateSelectView(PermissionRequiredMixin, ListView):
    permission_required = 'activities.add_activity'
    model = ActivityTemplate
    template_name = 'activities/activitytemplate_select.html'

class ActivityCreateView(CreateViewPermissionMixin, View):
    model = Activity
    template_name = 'activities/activity_create.html'

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
            # inject the author, faculty, and program into the form data
            Activity.objects.create(
                template = activity_template,
                author = request.user,
                faculty = request.user.faculty,
                response_json = form.cleaned_data,
            )
            return redirect('activities:view_activity')
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
    filename = "activities_export.xlsx"
    sheet_name = "Activities Data"
    json_fields_to_extract = ['response_json']

