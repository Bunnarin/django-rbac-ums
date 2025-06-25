from django import forms

def generate_dynamic_form_class(question_definitions, form_name="DynamicForm"):
    """
    Generates a Django Form class based on a list of question dictionaries.
    Each dictionary defines a form field.
    """
    form_fields = {}

    for i, field_def in enumerate(question_definitions):
        field_name = field_def.get('name', f'field_{i}')
        field_type = field_def.get('type')
        field_title = field_def.get('title')
        is_required = field_def.get('is_required', False)

        form_field = None

        if field_type == 'text':
            form_field = forms.CharField(
                label=field_title,
                required=is_required,
                max_length=field_def.get('maxLength'),
            )
        elif field_type == 'paragraph':
            form_field = forms.CharField(
                label=field_title,
                required=is_required,
                max_length=field_def.get('maxLength'),
                widget=forms.Textarea,
            )
        elif field_type == 'integer':
            min_val = field_def.get('min')
            max_val = field_def.get('max')

            form_field = forms.IntegerField(
                label=field_title,
                required=is_required,
                min_value=min_val,
                max_value=max_val,
            )
        elif field_type == 'decimal':
            min_val = field_def.get('min')
            max_val = field_def.get('max')

            form_field = forms.FloatField(
                label=field_title,
                required=is_required,
                min_value=min_val,
                max_value=max_val,
            )

        elif field_type == 'dropdown':
            choices_list = [(item, item) for item in field_def.get('choices', [])]
            form_field = forms.ChoiceField(
                label=field_title,
                required=is_required,
                choices=choices_list,
            )

        elif field_type == 'checkbox': # Multiple choice using SelectMultiple (multi-select dropdown)
            choices_list = [(item, item) for item in field_def.get('choices', [])]
            form_field = forms.MultipleChoiceField(
                label=field_title,
                required=is_required,
                choices=choices_list,
                widget=forms.CheckboxSelectMultiple(),
            )

        elif field_type == 'date':
            form_field = forms.DateField(
                label=field_title,
                required=is_required,
                widget=forms.DateInput(attrs={'type': 'date'}), # Renders as an HTML5 date picker
            )

        if form_field:
            form_fields[field_name] = form_field

    DynamicForm = type(
        form_name,
        (forms.Form,),
        form_fields,
    )
    return DynamicForm