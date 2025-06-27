import openpyxl
from io import BytesIO
from django.http import HttpResponse
import json
from datetime import datetime, date

def _get_nested_attr(obj, attr_path):
    """
    Safely retrieves a potentially nested attribute from a Django model instance.
    Handles ForeignKey relationships and returns None if any part of the path is missing.
    Example: _get_nested_attr(activity_obj, 'template.name')
    """
    attrs = attr_path.split('.')
    current_obj = obj
    for attr in attrs:
        if current_obj is None:
            return None # Stop if an intermediate object is None (e.g., no template linked)
        try:
            current_obj = getattr(current_obj, attr)
        except AttributeError:
            return None # Attribute does not exist
    return current_obj

def export_queryset_to_xlsx(queryset, fields_to_export, filename="data_export.xlsx", sheet_name="Exported Data"):
    """
    Exports a Django QuerySet to a single XLSX sheet.

    Args:
        queryset (QuerySet): The Django QuerySet (e.g., Activity.objects.all()).
        fields_to_export (list): A list of tuples, where each tuple is
                                  (model_attribute_path_string, "Excel Column Header").
                                  'model_attribute_path_string' can be a direct field name
                                  or a dotted path for related fields (e.g., 'template.name').
        filename (str): The desired filename for the XLSX file (e.g., "activities.xlsx").
        sheet_name (str): The name for the Excel sheet (default "Exported Data").
    """
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = sheet_name[:31].replace('/', '_').replace('\\', '_').replace('?', '_').replace('*', '_').replace('[', '_').replace(']', '_').replace(':', '_') # Max 31 chars, valid chars

    # Write headers
    headers = [header for _, header in fields_to_export]
    sheet.append(headers)

    # Write data rows
    for obj in queryset:
        row_data = []
        for field_path, _ in fields_to_export:
            value = _get_nested_attr(obj, field_path)

            if isinstance(value, (dict, list)):
                # Export JSONField content as a raw JSON string
                cell_value = json.dumps(value, separators=(',', ':'), ensure_ascii=False)
            elif isinstance(value, datetime):
                # Format datetime objects
                cell_value = value.strftime('%Y-%m-%d %H:%M:%S')
            elif isinstance(value, date):
                # Format date objects
                cell_value = value.strftime('%Y-%m-%d')
            elif value is None:
                cell_value = '' # Represent None as an empty string
            else:
                cell_value = str(value) # Convert other types to string

            row_data.append(cell_value)
        sheet.append(row_data)

    # Prepare the HTTP response
    output = BytesIO()
    workbook.save(output)
    output.seek(0) # Go to the beginning of the stream

    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response