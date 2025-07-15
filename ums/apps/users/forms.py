from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from apps.organization.models import Faculty, Program
User = get_user_model()

class CustomUserCreationForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('email', 'faculties', 'programs')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # If editing an existing user, set initial values for many-to-many fields
        if self.instance.pk:
            self.fields['faculties'].initial = self.instance.faculties.all()
            self.fields['programs'].initial = self.instance.programs.all()

    def clean(self):
        cleaned_data = super().clean()
        faculties = cleaned_data.get('faculties')
        programs = cleaned_data.get('programs')

        # Check if any programs are selected
        if faculties and programs:
            # Get all faculties from the selected programs
            program_faculties = Faculty.objects.filter(
                program__in=programs
            ).distinct()
            
            missing_faculties = program_faculties.exclude(id__in=[f.id for f in faculties])
            if missing_faculties.exists():
                raise ValidationError({
                    'programs': f"The selected programs include faculties that are not in the assigned faculties: {', '.join(str(f) for f in missing_faculties)}"
                })
        
        return cleaned_data

    def save(self, commit=False):
        # Get the many-to-many data before saving
        faculties = self.cleaned_data.pop('faculties', None)
        programs = self.cleaned_data.pop('programs', None)
        
        # Save the user instance   
        user = super().save(commit=commit)
        user.set_unusable_password()
        
        if commit:
            # Set the many-to-many relationships
            if faculties is not None:
                user.faculties.set(faculties)
            if programs is not None:
                user.programs.set(programs)
        
        return user