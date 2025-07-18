from django.urls import reverse_lazy
import openpyxl
import json
from io import BytesIO
from datetime import datetime, date
from django import forms
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse
from django.views.generic import View, ListView, DeleteView, CreateView, UpdateView
from django.utils import timezone
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import redirect

class BaseExportView(View):
    """
    Base view for exporting data to Excel format.
    
    This view provides a reusable implementation for exporting model data to Excel files,
    with support for nested attributes and JSON field extraction.
    
    Attributes:
        model: The Django model class to export from
        fields_to_export: List of tuples containing field paths and header names
        filename: Name of the exported Excel file
        sheet_name: Name of the main data sheet
        json_fields_to_extract: List of field paths to extract as separate JSON sheets
    """
    model = None
    fields_to_export = []
    filename = "export.xlsx"
    sheet_name = "Exported Data"
    json_fields_to_extract = []

    def get_queryset(self):
        """
        Get the queryset for export.
        
        Returns:
            QuerySet: Filtered queryset based on user permissions
        """
        if hasattr(self.model.objects, "for_user"):
            return self.model.objects.for_user(self.request)
        return super().get_queryset()

    def _get_nested_attr(self, obj, attr_path):
        """
        Get a nested attribute from an object using dot notation.
        
        Args:
            obj: The object to get attributes from
            attr_path: String representing the path to the attribute (e.g., 'user.profile.name')
            
        Returns:
            Any: The value of the nested attribute, or None if not found
        """
        attrs = attr_path.split('.')
        current_obj = obj
        for attr in attrs:
            if current_obj is None:
                return None
            try:
                current_obj = getattr(current_obj, attr)
            except AttributeError:
                return None
        return current_obj

    def _format_value_for_excel(self, value):
        """
        Format a value for Excel output.
        
        Args:
            value: The value to format
            
        Returns:
            str: Formatted value suitable for Excel
        """
        if isinstance(value, (dict, list)):
            return ", ".join(map(str, value))
        elif isinstance(value, datetime):
            if timezone.is_aware(value):
                target_timezone = timezone.get_current_timezone()
                value = value.astimezone(target_timezone)
            return value.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(value, date):
            if timezone.is_aware(value):
                target_timezone = timezone.get_current_timezone()
                value = value.astimezone(target_timezone)
            return value.strftime('%Y-%m-%d')
        elif value is None:
            return ''
        else:
            return str(value)

    def get(self, request, *args, **kwargs):
        """
        Handle GET request to export data to Excel.
        
        Args:
            request: Django HTTP request object
            
        Returns:
            HttpResponse: Excel file response
        """
        queryset = self.get_queryset()

        workbook = openpyxl.Workbook()

        # --- Main Data Sheet ---
        main_sheet = workbook.active
        main_sheet.title = self.sheet_name

        main_sheet_headers = [header for _, header in self.fields_to_export]
        main_sheet.append(main_sheet_headers)

        # --- Determine Context Headers for JSON Sheets ---
        json_context_fields_paths = []
        json_context_headers = []
        for field_path, header_name in self.fields_to_export:
            if field_path not in self.json_fields_to_extract:
                json_context_fields_paths.append(field_path)
                json_context_headers.append(header_name)

        # --- JSON Data Sheets Management ---
        json_schema_sheets_data = {}
        json_schema_counter = 0

        # --- Populate Main Sheet and Collect JSON Data ---
        for obj in queryset:
            main_row_data = []
            obj_json_context_values = [] # Store context values for the current object

            # First, collect context values for JSON sheets
            for field_path in json_context_fields_paths:
                value = self._get_nested_attr(obj, field_path)
                obj_json_context_values.append(self._format_value_for_excel(value))

            # Now, process all fields for the main sheet and extract JSON data for separate sheets
            for field_path, _ in self.fields_to_export:
                value = self._get_nested_attr(obj, field_path)

                # Always add the raw (formatted) value to the main sheet
                main_row_data.append(self._format_value_for_excel(value))

                # If this is a JSON field specified for extraction, process it for its own sheet
                if field_path in self.json_fields_to_extract:
                    if isinstance(value, dict) and value: # Only process non-empty dicts
                        schema_keys = tuple(sorted(value.keys()))

                        if schema_keys not in json_schema_sheets_data:
                            json_schema_counter += 1
                            sheet_title = f"{field_path.replace('_', ' ').title()} Data {json_schema_counter}"
                            valid_sheet_title = sheet_title[:31].replace('/', '_').replace('\\', '_').replace('?', '_').replace('*', '_').replace('[', '_').replace(']', '_').replace(':', '_')

                            # Combine context headers with dynamic JSON keys
                            combined_headers = json_context_headers + list(schema_keys)

                            json_schema_sheets_data[schema_keys] = {
                                'sheet_title': valid_sheet_title,
                                'headers': combined_headers, # Store combined headers
                                'rows': []
                            }

                        # Prepare row for the JSON-specific sheet: context values + formatted JSON values
                        json_dynamic_values = [self._format_value_for_excel(value.get(key, '')) for key in schema_keys]
                        combined_json_row_data = obj_json_context_values + json_dynamic_values

                        json_schema_sheets_data[schema_keys]['rows'].append(combined_json_row_data)

            main_sheet.append(main_row_data)

        # --- Create and Populate JSON-specific Sheets ---
        for schema_keys, data in json_schema_sheets_data.items():
            json_sheet = workbook.create_sheet(title=data['sheet_title'])
            json_sheet.append(data['headers']) # Append combined headers
            for row in data['rows']:
                json_sheet.append(row) # Append combined data rows

        # ... (rest of your response preparation code) ...
        output = BytesIO()
        workbook.save(output)
        output.seek(0)

        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="{self.filename}"'

        return response

class BaseTemplateCreateView(PermissionRequiredMixin, CreateView):
    """
    Base view for handling dynamic JSON field creation and updates
    via a frontend builder.
    
    Attributes:
        default_form_fields: List of fields to include in the form
        json_field_name_in_model: Name of the JSON field in the model (default: 'template_json')
        template_name: Name of the template to use for rendering (default: 'core/template_builder.html')
        model: The model class
        success_url_name: Name of the URL pattern to redirect to after success
    """
    default_form_fields = []
    json_field_name_in_model = 'template_json'
    template_name = 'core/template_builder.html'
    model = None

    def get_permission_required(self):
        """
        Get the permission required for this view.
        Returns different permissions for create vs update operations.
        
        Returns:
            list: List of permissions required
        """
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name.lower()
        return [f'{self.app_label}.add_{self.model_name}']

    def get_form_class(self):
        """
        Get the form class for this view.
        
        Returns:
            type: Form class
        """
        class Meta:
            model = self.model
            fields = self.default_form_fields

        DynamicModelForm = type(
            f"{self.model.__name__}Form",
            (forms.ModelForm,),
            {'Meta': Meta}
        )

        return DynamicModelForm

    def get_success_url(self):
        """
        Get the URL to redirect to after a successful form submission.
        
        Returns:
            str: URL to redirect to
        """
        return reverse_lazy(f'{self.app_label}:view_{self.model_name}')

    def form_valid(self, form):
        """
        Handle a valid form submission for both create and update operations.
        
        Args:
            form: Form instance
        
        Returns:
            HttpResponse: Response to return
        """
        # Get the JSON string from the request.POST
        template_json_str = self.request.POST.get(self.json_field_name_in_model)

        if template_json_str:
            try:
                json_data = json.loads(template_json_str)
                if not isinstance(json_data, list) or not json_data:
                    raise json.JSONDecodeError("JSON must be a non-empty array", "", 0)
                setattr(form.instance, self.json_field_name_in_model, json_data)
            except json.JSONDecodeError as e:
                form.add_error(None, ValidationError(
                    f"Invalid JSON data provided for {self.json_field_name_in_model}: {str(e)}"
                ))
                return self.form_invalid(form)
        else:
            form.add_error(None, ValidationError("Must have at least one question."))
            return self.form_invalid(form)

        return super().form_valid(form)

class BaseTemplateUpdateView(BaseTemplateCreateView, UpdateView):
    """
    Base view for updating a template.
    
    Attributes:
        model: Model to update
        actions: List of actions to include in the view
        template_name: Name of the template to use for rendering
        table_fields: List of fields to include in the table
    """
    def get_permission_required(self):
        """
        Get the permission required for this view.
        Returns different permissions for create vs update operations.
        
        Returns:
            list: List of permissions required
        """
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name.lower()
        return [f'{self.app_label}.change_{self.model_name}']

    def get_form_kwargs(self):
        """
        Add the instance to form kwargs if this is an update operation.
        """
        kwargs = super().get_form_kwargs()
        if hasattr(self, 'object'):
            kwargs['instance'] = self.object
        return kwargs
    
    def get_context_data(self, **kwargs):
        """
        Add template context data.
        """
        context = super().get_context_data(**kwargs)
        context['object'] = getattr(self, 'object', None)
        # Ensure the JSON field is available in the template
        if hasattr(self, 'object') and self.object:
            context['template_json'] = getattr(self.object, self.json_field_name_in_model, None)
        return context


class BaseListView(PermissionRequiredMixin, ListView):
    """
    Base view for displaying a list of objects.
    
    Attributes:
        model: Model to display
        actions: List of actions to include in the view
        template_name: Name of the template to use for rendering
        table_fields: List of fields to include in the table
    """
    model = None
    actions = []
    template_name = 'core/generic_list.html'
    table_fields = []

    def get_permission_required(self):
        """
        Get the permission required for this view.
        
        Returns:
            list: List of permissions required
        """
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name.lower()
        user = self.request.user
        for action in ["view", "change", "delete"]:
            if user.has_perm(f'{self.app_label}.{action}_{self.model_name}'):
                return [f'{self.app_label}.{action}_{self.model_name}']
        return [f'{self.app_label}.view_{self.model_name}'] # Default to view permission

    def get_context_data(self, **kwargs):
        """
        Get the context data for this view.
        
        Args:
            **kwargs: Keyword arguments
        
        Returns:
            dict: Context data
        """
        context = super().get_context_data(**kwargs)
        context['table_headers'] = self.table_fields
        context['table_fields'] = self.table_fields

        # check permission
        user = self.request.user
        for action in self.actions:
            if action == "export":
                url = f'{self.app_label}:export_{self.model_name}'
                context["export_url"] = url
                continue

            permission = f'{self.app_label}.{action}_{self.model_name}'
            if user.has_perm(permission):
                url = permission.replace('.', ':')
                context[f"{action}_url"] = url

        return context

    def get_queryset(self):
        """
        Get the queryset for this view.
        
        Returns:
            QuerySet: Filtered queryset based on user permissions
        """
        if hasattr(self.model.objects, "for_user"):
            return self.model.objects.for_user(self.request)
        return super().get_queryset()

class BaseCreateView(PermissionRequiredMixin, CreateView):
    """
    Mixin for views that require permission to add an object.
    
    Attributes:
        model: Model to create
        template_name: Name of the template to use for rendering
        fields: List of fields to include in the form
    """
    model = None
    template_name = 'core/generic_form.html'
    fields = []

    def get_permission_required(self):
        """
        Get the permission required for this view.
        
        Returns:
            list: List of permissions required
        """
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name.lower()
        return [f'{self.app_label}.add_{self.model_name}']

class BaseUpdateView(PermissionRequiredMixin, UpdateView):
    """
    Mixin for views that require permission to update an object.
    
    Attributes:
        model: Model to update
        pk_url_kwarg: Name of the URL keyword argument for the primary key
        template_name: Name of the template to use for rendering
    """
    model = None
    pk_url_kwarg = 'pk'
    template_name = 'core/generic_form.html'
    fields = []

    def get_permission_required(self):
        """
        Get the permission required for this view.
        
        Returns:
            list: List of permissions required
        """
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name.lower()
        """
        Dynamically determines the permission required based on the view's model.
        """
        return [f'{self.app_label}.change_{self.model_name}']

class BaseDeleteView(PermissionRequiredMixin, DeleteView):
    """
    Mixin for views that require permission to delete an object.
    
    Attributes:
        model: Model to delete
        pk_url_kwarg: Name of the URL keyword argument for the primary key
        template_name: Name of the template to use for rendering
    """
    model = None
    pk_url_kwarg = 'pk'
    template_name = 'core/generic_delete.html'

    def get_permission_required(self):
        """
        Get the permission required for this view.
        
        Returns:
            list: List of permissions required
        """
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name.lower()
        """
        Dynamically determines the permission required based on the view's model.
        """
        return [f'{self.app_label}.delete_{self.model_name}']

    def get_success_url(self):
        """
        Get the URL to redirect to after a successful deletion.
        
        Returns:
            str: URL to redirect to
        """
        return reverse_lazy(f'{self.app_label}:view_{self.model_name}')

    def get_context_data(self, **kwargs):
        """
        Get the context data for this view.
        
        Args:
            **kwargs: Keyword arguments
        
        Returns:
            dict: Context data
        """
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = f'{self.app_label}:view_{self.model_name}'
        return context

    def get_queryset(self):
        """
        Get the queryset for this view.
        
        Returns:
            QuerySet: Filtered queryset based on user permissions
        """
        if hasattr(self.model.objects, "for_user"):
            return self.model.objects.for_user(self.request)
        return super().get_queryset()

@require_POST
def set_faculty(request):
    """
    Set the selected faculty for the user.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    
    faculty_id = request.POST.get('faculty_id')
    
    if faculty_id:
        try:
            faculty_id = int(faculty_id)
            # Check if the faculty is in user's faculties
            if faculty_id not in request.user.faculties.values_list('id', flat=True):
                return JsonResponse({'success': False, 'error': 'Unauthorized faculty'}, status=403)
            request.session['selected_faculty'] = faculty_id
            return redirect(request.META.get('HTTP_REFERER', '/'))
            
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid faculty ID'}, status=400)
    
    return JsonResponse({'success': False, 'error': 'No faculty ID provided'}, status=400)

@require_POST
def set_program(request):
    """
    Set the selected program for the user.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    
    program_id = request.POST.get('program_id')
    if program_id:
        try:
            program_id = int(program_id)
            # Check if the program is in user's programs
            if program_id not in request.user.programs.values_list('id', flat=True):
                return JsonResponse({'success': False, 'error': 'Unauthorized program'}, status=403)
            request.session['selected_program'] = program_id
            return redirect(request.META.get('HTTP_REFERER', '/'))
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': 'Invalid program ID'}, status=400)
    
    return JsonResponse({'success': False, 'error': 'No program ID provided'}, status=400)
