from django import forms
from apps.organization.models import Program, Faculty
from .models import User, Student

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

        # filter permissions (this mean that the user creator would need to be in all the group first)
        self.fields['groups'].queryset = user.groups
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
        if faculties and programs:
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

    def save(self, commit=True):
        data = self.cleaned_data
        user = User.objects.create(
            first_name=data['first_name'], last_name=data['last_name'], email=data['email']
            )
        student = super().save(commit=False)
        student.user = user
        if commit:
            student.save()
        return student