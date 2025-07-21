from django.contrib.auth.models import Permission
from apps.core.views import BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView, BaseExportView
from .models import Student, Professor, CustomUser

class UserListView(BaseListView):
    model = CustomUser
    actions = ['export', 'add', 'change', 'delete']
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
        
        # filter affiliation
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

class UserExportView(BaseExportView):
    model = CustomUser
    fields_to_export = ['first_name', 'last_name', 'email', 'phone_number', 'faculties', 'programs']

class StudentListView(BaseListView):
    model = Student
    actions = ['export', 'add', 'change', 'delete']
    table_fields = ['user', 'faculty', 'program']

class StudentCreateView(BaseCreateView):
    model = Student
    fields = ['user', 'faculty', 'program']

class StudentUpdateView(BaseUpdateView):
    model = Student

class StudentDeleteView(BaseDeleteView):
    model = Student

class StudentExportView(BaseExportView):
    model = Student
    fields_to_export = ['user', 'faculty', 'program']

class ProfessorListView(BaseListView):
    model = Professor
    actions = ['export', 'add', 'change', 'delete']
    table_fields = ['user', 'faculty', 'program']

class ProfessorCreateView(BaseCreateView):
    model = Professor
    fields = ['user', 'faculty', 'program']

class ProfessorUpdateView(BaseUpdateView):
    model = Professor

class ProfessorDeleteView(BaseDeleteView):
    model = Professor

class ProfessorExportView(BaseExportView):
    model = Professor
    fields_to_export = ['user', 'faculty', 'program']

