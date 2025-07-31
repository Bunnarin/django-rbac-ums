from django.forms.formsets import BaseFormSet as DjangoBaseFormSet

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

class BaseFormSet(DjangoBaseFormSet):
    """
    Base formset that makes the request object available to all forms in the formset.
    The request object should be passed as a kwarg when initializing the formset.
    """
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
    
    def _construct_form(self, i, **kwargs):
        """
        Override to pass the request to each form in the formset.
        """
        form = super()._construct_form(i, **kwargs)
        if hasattr(self, 'request') and self.request is not None:
            form.request = self.request
        return form