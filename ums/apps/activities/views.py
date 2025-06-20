from django.views.generic import ListView, View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import PermissionRequiredMixin
from .models import ActivityTemplate, Activity
from .forms import generate_dynamic_form_class
# Create your views here.
class ActivityListView(PermissionRequiredMixin, ListView):
    model = Activity
    template_name = 'activities/activity_list.html'
    permission_required = 'activities.view_activity'

    def get_queryset(self):
        return self.model.secure_objects.for_user(self.request.user) # type: ignore

class ActivityTemplateListView(PermissionRequiredMixin, ListView):
    permission_required = 'activities.add_activity'
    model = ActivityTemplate
    template_name = 'activities/activity_template_list.html'


class ActivityCreateView(PermissionRequiredMixin, View):
    template_name = 'activities/activity_create.html'
    permission_required = 'activities.add_activity'

    def get(self, request, template_pk):
        # get the json
        activity_template = get_object_or_404(ActivityTemplate, pk=template_pk)
        template_json = activity_template.template_json
        Form = generate_dynamic_form_class(template_json)
        form = Form()
        # The title is now attached to the form class itself
        return render(request, self.template_name, {'form': form, 'form_title': activity_template.name})

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
            return redirect('activities:list')
        else:
            return render(request, self.template_name, {'form': form, 'form_title': activity_template.name})