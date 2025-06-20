from pathlib import Path
from django import forms
from django.forms.widgets import Textarea, CheckboxSelectMultiple

def generate_dynamic_form_class(question_definitions, form_name="DynamicForm"):
    """
    Generates a Django Form class based on a list of question dictionaries.
    Each dictionary defines a form field.
    """
    form_fields = {}

    for i, field_def in enumerate(question_definitions):
        # Generate a unique field name if not provided (e.g., from title)
        # Using a simple index-based name if title is repetitive or missing
        field_name = field_def.get('name', f'question_{i + 1}')

        # Sanitize name if derived from title (remove spaces, special chars)
        if 'title' in field_def and not 'name' in field_def:
            # Create a slug-like name from the title for consistency
            field_name_from_title = field_def['title'].lower().replace(' ', '_').replace('-', '_')
            field_name = ''.join(c for c in field_name_from_title if c.isalnum() or c == '_')
            # Ensure uniqueness if multiple questions have similar titles
            counter = 0
            original_field_name = field_name
            while field_name in form_fields:
                counter += 1
                field_name = f"{original_field_name}_{counter}"

        # Get common field properties
        field_type = field_def.get('type')
        field_title = field_def.get('title', field_name.replace('_', ' ').title())
        field_description = field_def.get('description', '') # Optional description
        is_required = field_def.get('is_required', False) # New key for required
        initial_value = field_def.get('default')

        form_field = None

        if field_type == 'str':
            widget = None
            if field_def.get('widget') == 'textarea':
                widget = Textarea

            form_field = forms.CharField(
                label=field_title,
                help_text=field_description,
                required=is_required,
                max_length=field_def.get('maxLength'),
                initial=initial_value,
                widget=widget
            )
        elif field_type == 'int':
            form_field = forms.IntegerField(
                label=field_title,
                help_text=field_description,
                required=is_required,
                min_value=field_def.get('min'), # Using 'min' as per new schema
                max_value=field_def.get('max'), # Using 'max' as per new schema
                initial=initial_value
            )
        elif field_type == 'float':
            form_field = forms.FloatField(
                label=field_title,
                help_text=field_description,
                required=is_required,
                min_value=field_def.get('min'),
                max_value=field_def.get('max'),
                initial=initial_value
            )
        elif field_type == 'enum': # Single choice dropdown
            choices_list = [(item, item) for item in field_def.get('choices', [])]
            form_field = forms.ChoiceField(
                label=field_title,
                help_text=field_description,
                required=is_required,
                choices=choices_list,
                initial=initial_value
            )
        elif field_type == 'enumList': # Multiple choice checkboxes/multi-select
            choices_list = [(item, item) for item in field_def.get('choices', [])]
            form_field = forms.MultipleChoiceField(
                label=field_title,
                help_text=field_description,
                required=is_required,
                choices=choices_list,
                widget=CheckboxSelectMultiple,
                initial=initial_value,
            )

        if form_field:
            form_fields[field_name] = form_field
        else:
            print(f"Warning: Field '{field_name}' with type '{field_type}' not supported or malformed. Skipping.")

    # Create the dynamic form class using type()
    # The form_name can be passed as an argument or derived from context
    DynamicForm = type(
        form_name,
        (forms.Form,),
        form_fields
    )

    # We removed the form_title attribute since the top-level schema object is gone.
    # The view will now provide the form title (e.g., from activity_template.name).

    return DynamicForm