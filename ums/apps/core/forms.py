from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field

def get_grid_form(model_form_class):
    class GridForm(model_form_class):
        def __init__(self, *args, **kwargs):
            request = kwargs.pop('request', None)
            print(request)
            super().__init__(*args, **kwargs)
            self.helper = FormHelper()
            self.helper.form_tag = False
            
            # Create a single row with all fields inline
            self.helper.layout = Layout(
                Div(
                    *[Field(field_name, wrapper_class='form-group') 
                      for field_name in self.fields],
                    css_class='d-flex flex-nowrap'
                )
            )
            
    return GridForm

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