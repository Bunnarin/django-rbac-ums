import openpyxl
import json
from io import BytesIO
from django.http import HttpResponse
from django.views.generic import View
from datetime import datetime, date

class BaseExportView(View):
    model = None
    fields_to_export = []
    filename = "export.xlsx"
    sheet_name = "Exported Data"
    json_fields_to_extract = []

    def get_queryset(self):
        # ... (existing get_queryset method) ...
        if self.model is None:
            raise NotImplementedError("Subclasses must define 'model'.")
        return self.model.objects.for_user(self.request.user)

    def _get_nested_attr(self, obj, attr_path):
        # ... (existing _get_nested_attr method) ...
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
        # ... (existing _format_value_for_excel method) ...
        if isinstance(value, (dict, list)):
            return ", ".join(map(str, value))
        elif isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(value, date):
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
        # These are the fields from fields_to_export that are NOT JSON fields
        # and thus serve as identifying context for the JSON data.
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

class BaseTemplateBuilderMixin:
    """
    Mixin for Django Create/Update Views that handle dynamic JSON field creation
    via a frontend builder.

    It expects:
    - A hidden input field in the form with the name matching the `json_field_name_in_model`.
    - JavaScript on the frontend to populate this hidden input with a JSON string.
    """
    json_field_name_in_model = 'template_json' # Default field name in the model

    def form_valid(self, form):
        # Get the JSON string from the request.POST (from the hidden input field)
        template_json_str = self.request.POST.get(self.json_field_name_in_model)

        if template_json_str:
            try:
                # Parse the JSON string into a Python list/dict
                setattr(form.instance, self.json_field_name_in_model, json.loads(template_json_str))
            except json.JSONDecodeError:
                # Add a form error if the JSON is invalid
                form.add_error(None, ValidationError(f"Invalid JSON data provided for {self.json_field_name_in_model}."))
                return self.form_invalid(form)
        else:
            # If no JSON data, default to an empty list (or whatever your model default is)
            setattr(form.instance, self.json_field_name_in_model, [])

        return super().form_valid(form)