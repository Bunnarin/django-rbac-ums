from django.views.generic import ListView, View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import PermissionRequiredMixin
from apps.core.views import BaseExportView
from apps.core.forms import generate_dynamic_form_class
from .models import Activity, ActivityTemplate
# Create your views here.
class ActivityListView(ListView):
    model = Activity
    template_name = 'activities/activity_list.html'
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        if user.has_perm('activities.view_activity') or \
            user.has_perm('activities.change_activity') or \
            user.has_perm('activities.delete_activity'):
            return self.model.secure_objects.for_user(user) # type: ignore

        return self.model.secure_objects.none() # type: ignore


class ActivityTemplateSelectView(PermissionRequiredMixin, ListView):
    permission_required = 'activities.add_activity'
    model = ActivityTemplate
    template_name = 'activities/activitytemplate_select.html'


class ActivityCreateView(PermissionRequiredMixin, View):
    permission_required = 'activities.add_activity'
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
                faculty = request.user.profile.faculty,
                program = request.user.profile.program,
                response_json = form.cleaned_data,
            )
            return redirect('activities:activity-list')
        else:
            return render(request, self.template_name, {'form': form})

class ActivityExportView(BaseExportView):
    model = Activity
    fields_to_export = [
        ('template', 'Type'),
        ('author', 'Author'),
        ('created_at', 'Created At'),
        ('faculty', 'Faculty'),
        ('program', 'Program'),
        ('response_json', 'Response'),
    ]
    filename = "activities_data_export.xlsx"
    sheet_name = "Activities Data"
    json_fields_to_extract = ['response_json']

