from apps.core.views import BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView, BaseImportView
from .models import Student, User
from .forms import UserForm, StudentForm

class UserListView(BaseListView):
    model = User
    table_fields = ['first_name', 'last_name', 'email']
    object_actions = [('✏️', 'users:change_user', None), ('🗑️', 'users:delete_user', None)]
    actions = [('+', 'users:add_user', None),
               ('import', 'users:import_user', 'add_user')]

    def get_queryset(self):
        return super().get_queryset().exclude(student__isnull=False)

class UserImportView(BaseImportView):
    model = User
    form_class = UserForm

class UserCreateView(BaseCreateView):
    model = User
    form_class = UserForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs

class UserUpdateView(UserCreateView, BaseUpdateView):
    pass

class UserDeleteView(BaseDeleteView):
    model = User

class StudentListView(BaseListView):
    model = Student
    table_fields = ['user.first_name', 'user.last_name', '_class', 'user.email']
    object_actions = [
        ('✏️', 'users:change_student', None), 
        ('🗑️', 'users:delete_student', None), 
        ('score', 'academic:view_score', None)
    ]
    actions = [('+', 'users:add_student', None),
               ('import', 'users:import_student', 'add_student')]

class StudentImportView(BaseImportView):
    model = Student
    form_class = StudentForm
    
class StudentCreateView(BaseCreateView):
    model = Student
    form_class = StudentForm

class StudentUpdateView(StudentCreateView, BaseUpdateView):
    def get_initial(self):
        initial = super().get_initial()
        student = self.get_object()
        user = student.user
        initial.update({
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'new_user': False,
        })
        return initial

class StudentDeleteView(BaseDeleteView):
    model = Student