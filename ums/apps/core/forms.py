from django import forms

def generate_dynamic_form_class(json_template, form_name="DynamicForm"):
    """
    Generates a Django Form class based on a list of question dictionaries.
    Each dictionary defines a form field.

    Args:
        json_template: List of dictionaries, where each dictionary defines a form field
            Each dictionary should contain:
            - type: String indicating the field type (text, paragraph, integer, etc.)
            - label: Display label for the field
            - required: Boolean indicating if the field is required
            - choices: Optional list of choices for dropdown/checkbox fields
        form_name: Name of the generated form class (default: "DynamicForm")
    
    Returns:
        type: New Django Form class with fields defined by the template
    """
    form_fields = {}

    for field_def in json_template:
        field_type = field_def.get('type')
        fieldKwargs = {
            'label': field_def.get('label'),
            'required': field_def.get('required'),
        }

        choices = [(item, item) for item in field_def.get('choices', [])]
        if choices:
            fieldKwargs['choices'] = choices

        form_field = None
        match field_type:
            case 'text': form_field = forms.CharField(**fieldKwargs)
            case 'paragraph': form_field = forms.CharField(widget=forms.Textarea(), **fieldKwargs)
            case 'integer': form_field = forms.IntegerField(**fieldKwargs)
            case 'decimal': form_field = forms.FloatField(**fieldKwargs)
            case 'dropdown': form_field = forms.ChoiceField(**fieldKwargs)
            case 'checkbox': form_field = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple(), **fieldKwargs)
            case 'date': form_field = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), **fieldKwargs)

        if form_field:
            label = field_def.get('label')
            form_fields[label] = form_field

    DynamicForm = type(
        form_name,
        (forms.Form,),
        form_fields,
    )
    return DynamicForm