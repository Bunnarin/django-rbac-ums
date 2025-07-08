from django.urls import reverse_lazy
import openpyxl
import json
from io import BytesIO
from datetime import datetime, date
from django import forms
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.views.generic import View, ListView, DeleteView, CreateView
from django.utils import timezone
from django.contrib.auth.mixins import PermissionRequiredMixin

class BaseExportView(View):
    model = None
    fields_to_export = []
    filename = "export.xlsx"
    sheet_name = "Exported Data"
    json_fields_to_extract = []

    def get_queryset(self):
        if hasattr(self.model.objects, "for_user"):
            return self.model.objects.for_user(self.request.user)
        return super().get_queryset()

    def _get_nested_attr(self, obj, attr_path):
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
        queryset = self.get_queryset()

        workbook = openpyxl.Workbook()

        # --- Main Data Sheet ---
        main_sheet_name = self.sheet_name[:31].replace('/', '_').replace('\\', '_').replace('?', '_').replace('*', '_').replace('[', '_').replace(']', '_').replace(':', '_')
        main_sheet = workbook.active
        main_sheet.title = main_sheet_name

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

class BaseTemplateBuilderView(PermissionRequiredMixin, CreateView):
    """
    Mixin for Django Create/Update Views that handle dynamic JSON field creation
    via a frontend builder.

    It expects:
    - A hidden input field in the form with the name matching the `json_field_name_in_model`.
    - JavaScript on the frontend to populate this hidden input with a JSON string.
    """
    default_form_fields = []
    json_field_name_in_model = 'template_json'
    template_name = 'core/template_builder.html'

    def get_permission_required(self):
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name.lower()
        return [f'{self.app_label}.add_{self.model_name}']

    def get_form_class(self):
        """
        Dynamically generates a ModelForm class based on the view's 'model' attribute.
        """
        class Meta:
            model = self.model  # <--- This is the key: uses the model from the view instance
            fields = self.default_form_fields

        DynamicModelForm = type(
            f"{self.model.__name__}Form", # Name for the dynamic form class (e.g., ActivityTemplateForm)
            (forms.ModelForm,),            # Base classes for the new form
            {'Meta': Meta}                 # Attributes for the new form (Meta class)
        )

        return DynamicModelForm

    def get_success_url(self):
        return reverse_lazy(f'{self.app_label}:view_{self.model_name}')

    def form_valid(self, form):
        # Get the JSON string from the request.POST (from the hidden input field)
        template_json_str = self.request.POST.get(self.json_field_name_in_model)

        if template_json_str:
            try:
                setattr(form.instance, self.json_field_name_in_model, json.loads(template_json_str))
            except json.JSONDecodeError:
                form.add_error(None, ValidationError(f"Invalid JSON data provided for {self.json_field_name_in_model}."))
                return self.form_invalid(form)
        else:
            setattr(form.instance, self.json_field_name_in_model, [])

        return super().form_valid(form)

class BaseListView(PermissionRequiredMixin, ListView):
    model = None
    actions = []
    template_name = 'core/generic_list.html'
    table_fields = []

    def get_permission_required(self):
        """
        user can view if they have view, update, or delete permissions
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
            return self.model.objects.for_user(self.request.user)
        return super().get_queryset()

class CreateViewPermissionMixin(PermissionRequiredMixin):
    """
    Mixin for views that require permission to add an object.
    Checks if the user has the 'add' permission for the model.
    """
    def get_permission_required(self):
        """
        Dynamically determines the permission required based on the view's model.
        """
        if not hasattr(self, 'model') or not self.model:
            raise AttributeError(
                "AddViewPermissionMixin requires the view to have a 'model' attribute."
            )

        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name.lower()
        return [f'{self.app_label}.add_{self.model_name}']

class UpdateViewPermissionMixin(PermissionRequiredMixin):
    """
    Mixin for views that require permission to add an object.
    Checks if the user has the 'add' permission for the model.
    """
    def get_permission_required(self):
        """
        Dynamically determines the permission required based on the view's model.
        """
        if not hasattr(self, 'model') or not self.model:
            raise AttributeError(
                "AddViewPermissionMixin requires the view to have a 'model' attribute."
            )

        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name.lower()
        return [f'{self.app_label}.change_{self.model_name}']

class BaseDeleteView(PermissionRequiredMixin, DeleteView):
    """
    Mixin for views that require permission to add an object.
    Checks if the user has the 'add' permission for the model.
    """
    model = None
    pk_url_kwarg = 'pk'
    template_name = 'core/generic_delete.html'

    def get_permission_required(self):
        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name.lower()
        """
        Dynamically determines the permission required based on the view's model.
        """
        return [f'{self.app_label}.delete_{self.model_name}']

    def get_success_url(self):
        return reverse_lazy(f'{self.app_label}:view_{self.model_name}')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cancel_url"] = f'{self.app_label}:view_{self.model_name}'
        return context

    def get_queryset(self):
        if hasattr(self.model.objects, "for_user"):
            return self.model.objects.for_user(self.request.user)
        return super().get_queryset()
