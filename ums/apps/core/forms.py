from django import forms

def generate_dynamic_form_class(json_template, form_name="DynamicForm"):
    """
    Generates a Django Form class based on a list of question dictionaries.

    Args:
        json_template: List of dictionaries, where each dictionary defines a form field
            Each dictionary should contain:
            - type: String indicating the field type (text, paragraph, integer, decimal, date, datetime, list, dropdown, checkbox)
            - label: Display label for the field
            - required: Boolean indicating if the field is required
            - choices: Optional string of choices for dropdown/checkbox fields (comma-separated)
        form_name: Name of the generated form class (default: "DynamicForm")
    
    Returns:
        type: New Django Form class with fields defined by the template
    """
    form_fields = {}

    for field_def in json_template:
        field_type = field_def.get('type')
        fieldKwargs = {
            'label': field_def.get('label'),
            'required': field_def.get('required', False),
        }

        # Handle choices for dropdown and checkbox fields
        choices_str = field_def.get('choices', '')
        if choices_str and field_type in ['dropdown', 'checkbox']:
            # Split by comma and create choice tuples
            choices = [(choice.strip(), choice.strip()) for choice in choices_str.split('\n') if choice.strip()]
            fieldKwargs['choices'] = choices

        form_field = None
        match field_type:
            case 'text':
                form_field = forms.CharField(**fieldKwargs)
            case 'paragraph':
                form_field = forms.CharField(widget=forms.Textarea(attrs={'rows': 4}), **fieldKwargs)
            case 'integer':
                form_field = forms.IntegerField(**fieldKwargs)
            case 'decimal':
                form_field = forms.DecimalField(**fieldKwargs)
            case 'date':
                form_field = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}), **fieldKwargs)
            case 'datetime':
                form_field = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), **fieldKwargs)
            case 'list':
                form_field = ListField(**fieldKwargs)
            case 'dropdown':
                if 'choices' in fieldKwargs:
                    form_field = forms.ChoiceField(**fieldKwargs)
            case 'checkbox':
                if 'choices' in fieldKwargs:
                    form_field = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple(), **fieldKwargs)

        if form_field:
            # Use a clean field name based on the label
            field_name = field_def.get('label', '').lower().replace(' ', '_').replace('-', '_')
            # Ensure field name is valid
            if not field_name or not field_name.replace('_', '').isalnum():
                field_name = f"field_{len(form_fields)}"
            form_fields[field_name] = form_field

    DynamicForm = type(
        form_name,
        (forms.Form,),
        form_fields,
    )
    return DynamicForm