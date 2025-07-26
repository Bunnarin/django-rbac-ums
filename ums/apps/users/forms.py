from django import forms
from django.db.models import Q
from django.contrib.auth.models import Permission
from braces.forms import UserKwargModelFormMixin
from apps.organization.models import Program, Faculty
from apps.academic.models import Class
from .models import CustomUser, Student

class UserForm(UserKwargModelFormMixin, forms.ModelForm):
    """
    Filter the user permissions based on user's own permission set.
    the mixin automate the popping of the user from the kwargs recieved from the other view that passed it
    """
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'faculties', 'programs', 'is_staff', 'groups', 'user_permissions']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # filter permissions
        self.fields['groups'].queryset = self.user.groups

        user_perms_direct = self.user.user_permissions.all()
        user_perms_via_groups = Permission.objects.filter(group__in=self.user.groups.all())
        allowed_permissions_qs = (user_perms_direct | user_perms_via_groups).distinct()

        extended_permissions_qs = Permission.objects.filter(
            Q(codename="access_faculty_wide") |
            Q(codename="access_program_wide")
        ).distinct()

        if self.user.has_perm("users.access_global") or self.user.has_perm("users.access_faculty_wide"):
            allowed_permissions_qs = (allowed_permissions_qs | extended_permissions_qs).distinct()

        self.fields['user_permissions'].queryset = allowed_permissions_qs.select_related("content_type")
        # filter affiliations
        if self.user.has_perm('users.access_global'):
            # no modification
            pass
        elif self.user.has_perm('users.access_faculty_wide'):
            self.fields['faculties'].queryset = self.user.faculties.all()
            self.fields['programs'].queryset = Program.objects.filter(
                faculty=self.user.faculties.all()
                )
        else:
            print(self.user.faculties.all())
            self.fields['faculties'].queryset = self.user.faculties.all()
            self.fields['programs'].queryset = self.user.programs.all()
    
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
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=False)
    phone_number = forms.CharField(required=False)
    
    class Meta:
        model = Student
        fields = ['_class']