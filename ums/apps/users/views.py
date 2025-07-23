from django.contrib.auth.models import Permission
from apps.core.views import BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView
from apps.organization.models import Faculty
from .models import Student, Professor, CustomUser

class UserListView(BaseListView):
    model = CustomUser
    table_fields = ['username', 'first_name', 'last_name', 'email', 'phone_number']

class UserCreateView(BaseCreateView):
    model = CustomUser
    fields = ['first_name', 'last_name', 'email', 'phone_number', 'faculties', 'programs', 'groups', 'user_permissions']
    
    def form_valid(self, form):
        """
        validate user's faculties and programs
        """
        if form.is_valid():
            cleaned_data = form.cleaned_data
            faculties = cleaned_data.get('faculties')
            programs = cleaned_data.get('programs')
            if faculties and programs:
                program_faculties = Faculty.objects.filter(programs__in=programs).distinct()
                missing_faculties = program_faculties.exclude(id__in=[f.id for f in faculties])
                if missing_faculties.exists():
                    form.add_error('programs', f"The selected programs include faculties that are not in the assigned faculties: {', '.join(str(f) for f in missing_faculties)}")
                    return self.form_invalid(form)
        return super().form_valid(form)

    def get_form(self, form_class=None):
        """
        Filter the user permissions based on user's own permission set.
        Limit affiliation based on user's own affiliation.
        """
        form = super().get_form(form_class)

        user = self.request.user
        # filter permissions
        form.fields['groups'].queryset = user.groups
        form.fields['user_permissions'].queryset = Permission.objects.filter(group__in=user.groups.all())
        
        # filter affiliations
        if user.has_perm('users.access_global'):
            return form
        elif user.has_perm('users.access_faculty_wide'):
            form.fields['faculties'].queryset = user.faculties.all()
            form.fields['programs'].queryset = Program.objects.filter(
                faculty__in=user.faculties.all()
                )
        else:
            form.fields['faculties'].queryset = user.faculties.all()
            form.fields['programs'].queryset = user.programs.all()
        return form

class UserUpdateView(UserCreateView, BaseUpdateView):
    pass

class UserDeleteView(BaseDeleteView):
    model = CustomUser

class StudentListView(BaseListView):
    model = Student
    table_fields = ['user', '_class']
    actions = [('score', 'academic:view_score')]

class StudentCreateView(BaseCreateView):
    model = Student
    fields = ['_class']
    flat_fields = [('user', ['first_name', 'last_name', 'email', 'phone_number'])]

class StudentUpdateView(BaseUpdateView):
    model = Student

    def get_form(self, form_class=None):
        """
        this is for the edge case of learning center where they might want to reselect 
        the correct user after creating a duplicate due to the restriction in the createview
        """
        form = super().get_form(form_class)
        user = self.get_object().user
        form.fields['user'].queryset = CustomUser.objects.filter(
            first_name=user.first_name, last_name=user.last_name
            )
        return form

class StudentDeleteView(BaseDeleteView):
    model = Student

class ProfessorListView(BaseListView):
    model = Professor
    table_fields = ['user']

class ProfessorCreateView(BaseCreateView):
    model = Professor
    flat_fields = [('user', ['first_name', 'last_name', 'email'])]

    def get_form(self, form_class=None):
        """
        limit the queryset to only user that aren't students
        """
        form = super().get_form(form_class)
        form.fields['user'].queryset = CustomUser.objects.exclude(student__isnull=False)
        return form

class ProfessorUpdateView(BaseUpdateView):
    model = Professor

    def get_form(self, form_class=None):
        """
        limit the queryset to only user that aren't students
        """
        form = super().get_form(form_class)
        form.fields['user'].queryset = CustomUser.objects.exclude(student__isnull=False)
        return form

class ProfessorDeleteView(BaseDeleteView):
    model = Professor