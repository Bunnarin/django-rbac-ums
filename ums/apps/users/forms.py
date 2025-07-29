from django import forms
from django.core.exceptions import ValidationError
from braces.forms import UserKwargModelFormMixin
from apps.organization.models import Program, Faculty
from .models import User, Student

class UserForm(UserKwargModelFormMixin, forms.ModelForm):
    """
    Filter the user permissions based on user's own permission set.
    the mixin automate the popping of the user from the kwargs recieved from the other view that passed it
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'faculties', 'programs', 'is_staff', 'groups']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # filter permissions
        self.fields['groups'].queryset = self.user.groups

        # filter affiliations
        if self.user.has_perm('users.access_global'):
            # no modification
            pass
        elif self.user.has_perm('users.access_faculty_wide'):
            self.fields['programs'].queryset = Program.objects.filter(faculty=self.user.faculties)
        else:
            self.fields['programs'].queryset = self.user.programs
        self.fields['faculties'].queryset = self.user.faculties
    
    def clean(self):
        cleaned_data = super().clean()
        faculties = cleaned_data.get('faculties')
        programs = cleaned_data.get('programs')
        if faculties and programs:
            program_faculties = Faculty.objects.filter(programs__in=programs).distinct()
            missing_faculties = program_faculties.exclude(id__in=[f.id for f in faculties])
            if missing_faculties.exists():
                self.add_error('programs', f"The selected programs include faculties that are not in the assigned faculties")
        return cleaned_data

class StudentForm(forms.ModelForm):
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField(required=False)
    phone_number = forms.CharField(required=False)
    new_user = forms.BooleanField(required=False, initial=True)
    selected_user = forms.ChoiceField(required=False, disabled=True)
    
    class Meta:
        model = Student
        fields = ['_class']
    
    def clean(self):
        """
        this is to ensure the user does not typo name and to confirm their intention
        """
        data = super().clean()
        exist = User.objects.filter(first_name=data['first_name'], last_name=data['last_name']).exists()
        if exist and data['new_user']:
            duplicated_users = User.objects.filter(first_name=data['first_name'], last_name=data['last_name'])
            self.fields['selected_user'].choices = [(user.id, f"{user.email} {user.phone_number}") for user in duplicated_users]
            self.fields['selected_user'].disabled = False
            raise ValidationError({"new_user": "User already exists. please check name spelling OR uncheck THIS and select an existing user instead"})
        elif not exist and not data['new_user']:
            raise ValidationError({"new_user": "User does not exist. please check name spelling OR check THIS to create this user instead"})
        
        return data        

    def save(self, commit=True):
        data = self.cleaned_data
        if data['new_user']:
            user = User.objects.create(first_name=data['first_name'], last_name=data['last_name'])
        else:
            user = User.objects.get(pk=data['selected_user'])

        user.email = data['email']
        user.phone_number = data['phone_number']
        user.save()

        student = super().save(commit=False)
        student.user = user
        if commit:
            student.save()
        return student