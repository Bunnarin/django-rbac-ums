from django import forms
from django_jsonform.widgets import JSONFormWidget
from .models import Activity

def translate_json_to_schema(template_json):
    # the rest is string
    type_map = {
        "integer": "integer",
        "number": "number",
        "checkbox": "array",
    }
    schema = {
        "type": "object",
        "keys": {}
    }
    for field in template_json:
        schema['keys'][field['title']] = {}
        key = schema['keys'][field['title']]

        key["type"] = type_map[field['type']] if field['type'] in type_map else "string"
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

def get_json_form(template_json):
    class ActivityForm(forms.ModelForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.schema = translate_json_to_schema(template_json)
            self.fields['response'].widget = JSONFormWidget(schema=self.schema)

        class Meta:
            model = Activity
            fields = ['faculty', 'response']
    return ActivityForm