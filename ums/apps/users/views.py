from apps.core.views import BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView, BaseExportView
from .models import Student, Professor, CustomUser

class UserListView(BaseListView):
    model = CustomUser
    actions = ['export', 'add', 'change', 'delete']
    table_fields = ['username', 'first_name', 'last_name', 'email', 'phone_number']

class UserCreateView(BaseCreateView):
    model = CustomUser
    fields = ['first_name', 'last_name', 'email', 'phone_number', 'faculties', 'programs']
    
    def get_form(self, form_class=None):
        """
        Limit affiliation based on user's own affiliation
        """
        form = super().get_form(form_class)
        
        user_faculties = getattr(self.request.user, 'faculties', None)
        if user_faculties:
            form.fields['faculties'].queryset = user_faculties.all()
        else:
            form.fields['faculties'].queryset = Faculty.objects.none()
    
        user_programs = getattr(self.request.user, 'programs', None)
        if user_programs:
            form.fields['programs'].queryset = user_programs.all()
        else:
            form.fields['programs'].queryset = Program.objects.none()
        
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

