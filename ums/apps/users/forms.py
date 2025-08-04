from django import forms
from django.contrib.auth.models import Group
from apps.organization.models import Program, Faculty
from apps.academic.models import Class
from .models import User, Student
from .queryset import GroupQuerySet

class UserForm(forms.ModelForm):
    """
    Filter the user permissions based on user's own permission set.
    the mixin automate the popping of the user from the kwargs recieved from the other view that passed it
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'faculties', 'programs', 'groups', 'is_staff']
    
    def __init__(self, *args, request, **kwargs):
        user = request.user
        s = request.session
        super().__init__(*args, **kwargs)

        # Get all groups where the user has all permissions
        self.fields['groups'].queryset = GroupQuerySet(Group).for_user(user)

        # if the user.is_staff = False, remove is_staff field
        if not user.is_staff:
            self.fields.pop('is_staff')

        # filter affiliations
        if 'access_global' in s['permissions']:
            # no modification
            pass
        elif 'access_faculty_wide' in s['permissions']:
            self.fields['faculties'].queryset = user.faculties
            self.fields['programs'].queryset = Program.objects.filter(faculty__in=user.faculties.all())
        else:
            self.fields['faculties'].queryset = user.faculties
            self.fields['programs'].queryset = user.programs
    
    def clean(self):
        data = super().clean()
        # check affiliation integrity
        faculties = data.get('faculties')
        programs = data.get('programs')
        if (not faculties and not programs) or (faculties and not programs):
            return data
            
        program_faculties = Faculty.objects.filter(programs__in=programs).distinct()
        missing_faculties = program_faculties.exclude(id__in=[f.id for f in faculties])
        if missing_faculties.exists():
            self.add_error('programs', f"The selected programs include faculties that are not in the assigned faculties")
        
        return data

class StudentForm(forms.ModelForm):
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.EmailField()
    
    class Meta:
        model = Student
        fields = ['_class']      
    
    def __init__(self, *args, request, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['_class'].queryset = Class.objects.get_queryset(request=request)

    def save(self, commit=True):
        data = self.cleaned_data
        user, _ = User.objects.get_or_create(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
        )
        user.save()

        student = super().save(commit=False)
        student.user = user
        if commit:
            student.save()
        return student