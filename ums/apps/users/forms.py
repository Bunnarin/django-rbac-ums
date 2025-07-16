from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from apps.organization.models import Faculty
User = get_user_model()

class CustomUserCreationForm(forms.ModelForm):
    """
    Custom form for creating and updating user accounts.
    
    This form extends Django's ModelForm to handle user creation with additional
    validation for faculty and program relationships.
    
    Attributes:
        Meta:
            model: User model
            fields: Fields to include in the form (email, faculties, programs)
    
    Methods:
        __init__(): Initializes the form and sets initial values for existing users
        clean(): Validates that all program faculties are included in assigned faculties
        save(): Saves the user and handles many-to-many relationships
    
    Validation:
        - Ensures that all programs' faculties are included in the assigned faculties
        - Handles password setting for new users
    """

    class Meta:
        model = User
        fields = ('email', 'faculties', 'programs')

    def __init__(self, *args, **kwargs):
        """
        Initialize the form and set initial values for existing users.
        
        For existing users, sets the initial values for faculties and programs
        based on the current user's relationships.
        """
        super().__init__(*args, **kwargs)
        # If editing an existing user, set initial values for many-to-many fields
        if self.instance.pk:
            self.fields['faculties'].initial = self.instance.faculties.all()
            self.fields['programs'].initial = self.instance.programs.all()

    def clean(self):
        """
        Validate that all selected programs' faculties are included in assigned faculties.
        
        Raises:
            ValidationError: If any program's faculty is not included in assigned faculties
        """
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
        """
        Save the user and handle many-to-many relationships.
        
        Args:
            commit: Boolean indicating if changes should be saved immediately
            
        Returns:
            User: The saved user instance
        
        Notes:
            - Sets an unusable password for security reasons
            - Handles many-to-many relationships for faculties and programs
        """
        # Get the many-to-many data before saving
        faculties = self.cleaned_data.pop('faculties', None)
        programs = self.cleaned_data.pop('programs', None)
        
        # Save the user instance   
        user = super().save(commit=commit)
        user.set_unusable_password()
        
        if commit:
            # Set the many-to-many relationships
            if faculties:
                user.faculties.set(faculties)
            if programs:
                user.programs.set(programs)
        
        return user