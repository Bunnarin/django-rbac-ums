from django import forms
from django_jsonform.widgets import JSONFormWidget
from .models import Activity

class ActivityForm(forms.ModelForm):
    def __init__(self, schema=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['response_json'].widget = JSONFormWidget(schema=schema)

    class Meta:
        model = Activity
        fields = ['faculty', 'response_json']

def translate_json_to_schema(template_json):
    type_translation = {
        "text": "string",
        "paragraph": "string",
        "integer": "integer",
        "number": "number",
        "date": "string",
        "date-time": "string",
        "time": "string",
        "dropdown": "string",
        "checkbox": "array"
    }
    schema = {
        "type": "object",
        "keys": {}
    }
    for field in template_json:
        schema['keys'][field['title']] = {}
        key = schema['keys'][field['title']]
        key["type"] = type_translation[field['type']]
        key["required"] = field['required']

        match field['type']:
            case 'paragraph':
                key['widget'] = 'textarea'
            case 'date' | 'date-time' | 'time':
                key['widget'] = field['type']
            case 'dropdown':
                key['choices'] = field['choices']
            case 'checkbox':
                key['items'] = {
                    "type": "string",
                    "choices": field['choices'],
                    "widget": "multiselect"
                }
    return schema