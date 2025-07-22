from django import forms
from django_jsonform.widgets import JSONFormWidget

def translate_json_to_schema(template_json):
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

def get_json_form(template_json, model, fields, json_field):
    class JsonForm(forms.ModelForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields[json_field].widget = JSONFormWidget(
                schema=translate_json_to_schema(template_json)
            )
    
    MetaClass = type('Meta', (), {'model': model, 'fields': fields})
    JsonFormClass = type('JsonForm', (JsonForm,), {'Meta': MetaClass})
    return JsonFormClass