from django import forms
from django.core.exceptions import ValidationError
from apps.organization.models import Faculty

class CustomUserAdminForm(forms.ModelForm):
    """
    Custom form to validate that all selected programs' faculties are included in assigned faculties.
    """
    
    def clean(self):
        cleaned_data = super().clean()
        faculties = cleaned_data.get('faculties')
        programs = cleaned_data.get('programs')

        if faculties and programs:
            program_faculties = Faculty.objects.filter(
                program__in=programs
            ).distinct()
            missing_faculties = program_faculties.exclude(id__in=[f.id for f in faculties])
            if missing_faculties.exists():
                raise ValidationError({
                    'programs': f"The selected programs include faculties that are not in the assigned faculties: {', '.join(str(f) for f in missing_faculties)}"
                })
        
        return cleaned_data