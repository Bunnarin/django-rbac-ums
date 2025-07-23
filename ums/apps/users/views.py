from django.contrib.auth.models import Permission
from apps.core.views import BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView
from .models import Student, Professor, CustomUser

class UserListView(BaseListView):
    model = CustomUser
    table_fields = ['username', 'first_name', 'last_name', 'email', 'phone_number']

class UserCreateView(BaseCreateView):
    model = CustomUser
    fields = ['first_name', 'last_name', 'email', 'phone_number', 'faculties', 'programs', 'user_permissions']
    
    def get_form(self, form_class=None):
        """
        Filter the user permissions based on user's own permission set.
        Limit affiliation based on user's own affiliation.
        """
        form = super().get_form(form_class)

        user = self.request.user
        # filter permissions
        user_perms_direct = user.user_permissions.all()
        user_perms_via_groups = Permission.objects.filter(group__in=user.groups.all())
        user_perms = (user_perms_direct | user_perms_via_groups).distinct()
        form.fields['user_permissions'].queryset = user_perms
        
        # filter affiliations
        if user.has_perm('users.access_global'):
            return form
        elif user.has_perm('users.access_faculty_wide'):
            form.fields['faculties'].queryset = user.faculties.all()
            form.fields['programs'].queryset = Program.objects.filter(faculty__in=user.faculties.all())
        else:
            form.fields['faculties'].queryset = user.faculties.all()
            form.fields['programs'].queryset = user.programs.all()
        
        return form
    

class UserUpdateView(BaseUpdateView):
    model = CustomUser
    fields = ['first_name', 'last_name', 'email', 'phone_number', 'faculties', 'programs']

class UserDeleteView(BaseDeleteView):
    model = CustomUser

class StudentListView(BaseListView):
    model = Student
    table_fields = ['user', '_class', 'faculty', 'program']

class StudentCreateView(BaseCreateView):
    model = Student
    flat_fields = [('user', ['first_name', 'last_name', 'phone_number'])]

class StudentUpdateView(BaseUpdateView):
    model = Student

class StudentDeleteView(BaseDeleteView):
    model = Student

class ProfessorListView(BaseListView):
    model = Professor
    table_fields = ['user', 'faculty', 'program']

class ProfessorCreateView(BaseCreateView):
    model = Professor
    flat_fields = [('user', ['first_name', 'last_name', 'email'])]

class ProfessorUpdateView(BaseUpdateView):
    model = Professor

class ProfessorDeleteView(BaseDeleteView):
    model = Professor