from django.urls import reverse_lazy
import openpyxl
from io import BytesIO
from datetime import datetime, date
from django.http import HttpResponse, JsonResponse
from django.views.generic import View, ListView, DeleteView, CreateView, UpdateView
from django.utils import timezone
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.decorators.http import require_POST
from django.shortcuts import redirect
from apps.organization.models import Program

class BaseWriteView(PermissionRequiredMixin):
    """
    Mixin for views that require permission to add or update an object.
    """
    pk_url_kwarg = 'pk'
    fields = '__all__'
    
    def get_success_url(self):
        return reverse_lazy(f'{self.app_label}:view_{self.model_name}')
    
    def get_queryset(self):
        if hasattr(self.model.objects, "for_user"):
            return self.model.objects.for_user(self.request)
        return super().get_queryset()
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if not hasattr(form, 'faculty'):
            return form
            
        form.fields['faculty'].initial = self.request.session.get('selected_faculty')
        form.fields['program'].initial = self.request.session.get('selected_program')
        user = self.request.user
        if user.has_perm('users.access_global'):
            return form
        elif user.has_perm('users.access_faculty_wide'):
            form.fields['faculty'].queryset = user.faculties.all()
            form.fields['program'].queryset = Program.objects.filter(faculty__in=user.faculties.all())
        else:
            form.fields['faculty'].queryset = user.faculties.all()
            form.fields['program'].queryset = user.programs.all()
    
        return form

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
        """
        queryset = self.get_queryset()

        workbook = openpyxl.Workbook()

        # --- Main Data Sheet ---
        main_sheet = workbook.active
        main_sheet.title = self.sheet_name

        main_sheet_headers = [header for header in self.fields_to_export]
        main_sheet.append(main_sheet_headers)

        # --- Determine Context Headers for JSON Sheets ---
        json_context_fields_paths = []
        json_context_headers = []
        for header in self.fields_to_export:
            if header not in self.json_fields_to_extract:
                json_context_fields_paths.append(header)
                json_context_headers.append(header)

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
            for field_path in self.fields_to_export:
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

class BaseListView(PermissionRequiredMixin, ListView):
    """
    Base view for displaying a list of objects.
    """
    model = None
    actions = []
    template_name = 'core/generic_list.html'
    table_fields = []

    def get_permission_required(self):
        """
        Get the permission required for this view.
        """
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name.lower()
        user = self.request.user
        for action in ["view", "change", "delete"]:
            if user.has_perm(f'{self.app_label}.{action}_{self.model_name}'):
                return [f'{self.app_label}.{action}_{self.model_name}']
        return [f'{self.app_label}.view_{self.model_name}'] # Default to view permission

    def get_context_data(self, **kwargs):
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
        if hasattr(self.model.objects, "for_user"):
            return self.model.objects.for_user(self.request)
        return super().get_queryset()

class BaseCreateView(BaseWriteView, CreateView):
    """
    Mixin for views that require permission to add an object.
    """
    template_name = 'core/generic_form.html'
    def get_permission_required(self):
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name.lower()
        return [f'{self.app_label}.add_{self.model_name}']

class BaseUpdateView(BaseWriteView, UpdateView):
    """
    Mixin for views that require permission to update an object.
    """
    template_name = 'core/generic_form.html'
    def get_permission_required(self):
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name.lower()
        return [f'{self.app_label}.change_{self.model_name}']
        
class BaseDeleteView(BaseWriteView, DeleteView):
    """
    Mixin for views that require permission to delete an object.
    """
    template_name = 'core/generic_delete.html'

    def get_permission_required(self):
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name.lower()
        return [f'{self.app_label}.delete_{self.model_name}']

@require_POST
def set_faculty(request):
    """
    Set the selected faculty for the user.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    
    faculty_id = request.POST.get('faculty_id')
    try:
        faculty_id = int(faculty_id)
    except:
        # don't set anything if invalid
        return redirect(request.META.get('HTTP_REFERER', '/'))
    user = request.user
    authorized = user.has_perm('users.access_global')
    if not authorized and faculty_id not in user.faculties.values_list('id', flat=True):
        return JsonResponse({'success': False, 'error': 'Unauthorized faculty'}, status=403)
    request.session['selected_faculty'] = faculty_id
    # now set the program as well
    if authorized:
        new_program = Program.objects.filter(faculty_id=faculty_id).first()
    else:
        new_program = user.programs.filter(faculty_id=faculty_id).first()
    if new_program:
        request.session['selected_program'] = new_program.id

    return redirect(request.META.get('HTTP_REFERER', '/'))

@require_POST
def set_program(request):
    """
    Set the selected program for the user.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'success': False, 'error': 'Not authenticated'}, status=401)
    
    program_id = request.POST.get('program_id')
    try:
        program_id = int(program_id)
    except:
        # don't set anything if invalid
        return redirect(request.META.get('HTTP_REFERER', '/'))
    # Check if the program is in user's programs
    user = request.user
    authorized = user.has_perm('users.access_global') or user.has_perm('users.access_faculty_wide')
    if not authorized and program_id not in request.user.programs.values_list('id', flat=True):
        return JsonResponse({'success': False, 'error': 'Unauthorized program'}, status=403)
    request.session['selected_program'] = program_id
    return redirect(request.META.get('HTTP_REFERER', '/'))
