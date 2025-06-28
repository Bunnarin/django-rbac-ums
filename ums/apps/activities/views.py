from django.db.models.query import QuerySet
from django.views.generic import ListView, View, CreateView, DeleteView
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from apps.core.views import BaseExportView
from apps.core.forms import generate_dynamic_form_class
from apps.core.mixins.views import ListViewPermissionMixin, CreateViewPermissionMixin, TemplateBuilderMixin, DeleteViewPermissionMixin
from .models import Activity, ActivityTemplate
from .forms import ActivityTemplateForm
# Create your views here.
class ActivityListView(ListViewPermissionMixin, ListView):
    model = Activity
    template_name = 'core/generic_list.html' # Use the generic template

    def get_queryset(self):
        return self.model.objects.for_user(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['table_headers'] = ['Author', 'Faculty', 'Program', 'Type']
        context['table_fields'] = ['author', 'faculty', 'program', 'template']

        # check permission
        user = self.request.user
        for action in ["add",]:
            permission = f'{self.app_label}.{action}_{self.model_name}'
            if user.has_perm(permission):
                url = permission.replace('.', ':')
                context[f"{action}_url"] = url

        context['export_url'] = f'{self.app_label}:export_{self.model_name}'
        return context

class ActivityTemplateSelectView(PermissionRequiredMixin, ListView):
    model = ActivityTemplate
    permission_required = 'activities.add_activity'
    template_name = 'activities/activitytemplate_select.html'


class ActivityCreateView(CreateViewPermissionMixin, View):
    model = Activity
    template_name = 'core/generic_form.html'

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
    filename = "activities_export.xlsx"
    sheet_name = "Activities Data"
    json_fields_to_extract = ['response_json']

class ActivityTemplateCreateView(TemplateBuilderMixin, CreateView):
    model = ActivityTemplate
    form_class = ActivityTemplateForm
    template_name = 'core/template_builder.html'
    success_url = reverse_lazy('activities:view_activity')
    json_field_name_in_model = 'template_json'

class ActivityTemplateListView(ListViewPermissionMixin, ListView):
    model = ActivityTemplate
    template_name = 'core/generic_list.html' # Use the generic template

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['table_headers'] = ['Type']
        context['table_fields'] = ['name']

        # check permission
        user = self.request.user
        for action in ["add", "delete"]:
            permission = f'{self.app_label}.{action}_{self.model_name}'
            if user.has_perm(permission):
                url = permission.replace('.', ':')
                context[f"{action}_url"] = url

        return context

class ActivityTemplateDeleteView(DeleteViewPermissionMixin, DeleteView):
    model = ActivityTemplate
    pk_url_kwarg = 'template_pk'
    template_name = 'core/generic_delete.html'
    success_url = reverse_lazy('activities:view_activitytemplate')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = f'{self.app_label}:view_{self.model_name}'
        return context
