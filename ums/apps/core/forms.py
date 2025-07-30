from django.forms import ModelChoiceField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field
from apps.core.managers import RLSManager
from apps.users.managers import UserRLSManager

def json_to_schema(template_json):
    schema = {
        "type": "object",
        "keys": {}
    }

    # the rest is string
    type_map = {
        "integer": "integer",
        "number": "number",
        "checkbox": "array",
    }
    for field in template_json:
        schema['keys'][field['title']] = {}
        key = schema['keys'][field['title']]

        key["type"] = type_map.get(field['type']) or "string"
        key["required"] = field['required']

        match field['type']:
            case 'paragraph':
                key['widget'] = 'textarea'
            case 'date' | 'date-time' | 'time':
                key['format'] = field['type']
            case 'dropdown':
                key['choices'] = field['choices']
            case 'checkbox':
                key['items'] = {
                    "type": "string",
                    "choices": field['choices'],
                    "widget": "multiselect"
                }
    return schema