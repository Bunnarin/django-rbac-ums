from django.views.generic import ListView, View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import PermissionRequiredMixin
from apps.core.views import BaseExportView, BaseTemplateCreateView, BaseTemplateUpdateView, BaseDeleteView, BaseListView
from apps.core.forms import generate_dynamic_form_class
from apps.organization.models import Faculty
from .models import Activity, ActivityTemplate

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
    actions = ["add", "export", "delete", "change"]
    table_fields = ['author', 'faculty', 'template']

class ActivityTemplateSelectView(ListView):
    """
    View for selecting an activity template.
    
    Allows users to choose from available activity templates before creating a new activity.
    
    Attributes:
        model: The ActivityTemplate model to display
        template_name: Template used for rendering the selection view
    """
    model = ActivityTemplate
    template_name = 'core/generic_select.html'
    
    def get_context_data(self, **kwargs):
        """
        Get context data for the template selection view.
        
        Args:
            **kwargs: Additional keyword arguments
            
        Returns:
            dict: Context data with redirect URL
        """
        context = super().get_context_data(**kwargs)
        context["redirect_url"] = f'activities:submit_activity'
        return context

class ActivityCreateView(PermissionRequiredMixin, View):
    """
    View for creating new activities.
        
    Attributes:
        model: The Activity model being created
        template_name: Template used for rendering the creation form
    """
    model = Activity
    template_name = 'core/generic_form.html'
    permission_required = 'activities.add_activity'

    def get(self, request, template_pk):
        activity_template = get_object_or_404(ActivityTemplate, pk=template_pk)
        template_json = activity_template.template_json
        Form = generate_dynamic_form_class(template_json)
        form = Form()
        return render(request, self.template_name, {'form': form})

    def post(self, request, template_pk):
        """
        Handle POST request for activity creation.
        
        Args:
            request: Django HTTP request object
            template_pk: Primary key of the selected template
            
        Returns:
            HttpResponse: Redirect to activity list or form with errors
        """
        activity_template = get_object_or_404(ActivityTemplate, pk=template_pk)
        template_json = activity_template.template_json
        Form = generate_dynamic_form_class(template_json)
        form = Form(request.POST)

        if form.is_valid():
            faculty_id = request.session.get('selected_faculty')
            faculty = Faculty.objects.get(id=faculty_id) if faculty_id else None
            Activity.objects.create(
                template = activity_template,
                author = request.user,
                faculty = faculty,
                response_json = form.cleaned_data,
            )
            return redirect('activities:view_activity')
        else:
            return render(request, self.template_name, {'form': form})

class ActivityUpdateView(PermissionRequiredMixin, View):
    """
    View for updating activities.
    
    Extends ActivityCreateView and BaseUpdateView to provide activity update functionality.
    
    Attributes:
        model: The Activity model
    """
    model = Activity
    template_name = 'core/generic_form.html'
    permission_required = 'activities.add_activity'
    
    def get(self, request, pk):
        activity = get_object_or_404(Activity, pk=pk)
        template_json = activity.template.template_json
        response_json = activity.response_json
        Form = generate_dynamic_form_class(template_json)
        form = Form(response_json)
        return render(request, self.template_name, {'form': form})
    
    def post(self, request, pk):
        """
        Handle POST request for activity creation.
        
        Args:
            request: Django HTTP request object
            template_pk: Primary key of the selected template
            
        Returns:
            HttpResponse: Redirect to activity list or form with errors
        """
        activity = get_object_or_404(Activity, pk=pk)
        activity_template = activity.template
        template_json = activity_template.template_json
        Form = generate_dynamic_form_class(template_json)
        form = Form(request.POST)

        if form.is_valid():
            faculty_id = request.session.get('selected_faculty')
            faculty = Faculty.objects.get(id=faculty_id) if faculty_id else None
            
            activity.author = request.user
            activity.faculty = faculty
            activity.response_json = form.cleaned_data
            activity.save()
            
            return redirect('activities:view_activity')
        else:
            return render(request, self.template_name, {'form': form})

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
    """
    View for deleting activities.
    
    Extends BaseDeleteView to provide activity deletion functionality.
    
    Attributes:
        model: The Activity model
    """
    model = Activity

class ActivityTemplateCreateView(BaseTemplateCreateView):
    """
    View for creating activity templates.
    
    Extends BaseTemplateBuilderView to provide template creation functionality.
    
    Attributes:
        model: The ActivityTemplate model
        default_form_fields: Default form fields to include
        json_field_name_in_model: Name of the JSON field in the model
    """
    model = ActivityTemplate
    default_form_fields = ['name']
    json_field_name_in_model = 'template_json'

class ActivityTemplateListView(BaseListView):
    """
    View for listing activity templates.
    
    Extends BaseListView to provide a filtered list of activity templates.
    
    Attributes:
        model: The ActivityTemplate model
        actions: List of available actions (add, delete)
        table_fields: Fields to display in the template list
    """
    model = ActivityTemplate
    actions = ["add", "delete", "change"]
    table_fields = ['name']

class ActivityTemplateUpdateView(BaseTemplateUpdateView):
    """
    View for updating activity templates.
    
    Extends BaseUpdateView to provide template update functionality.
    
    Attributes:
        model: The ActivityTemplate model
    """
    model = ActivityTemplate
    default_form_fields = ['name']
    json_field_name_in_model = 'template_json'

class ActivityTemplateDeleteView(BaseDeleteView):
    """
    View for deleting activity templates.
    
    Extends BaseDeleteView to provide template deletion functionality.
    
    Attributes:
        model: The ActivityTemplate model
    """
    model = ActivityTemplate
