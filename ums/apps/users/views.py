from apps.core.views import BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView, BaseImportView
from braces.views import UserFormKwargsMixin
from .models import Student, User
from .forms import UserForm, StudentForm

class UserListView(BaseListView):
    model = User
    table_fields = ['first_name', 'last_name', 'is_professor', 'is_staff', 'email', 'phone_number']
    object_actions = [('✏️', 'users:change_user', None), ('🗑️', 'users:delete_user', None)]
    actions = [('+', 'users:add_user', None),
               ('import', 'users:import_user', 'users.add_user')]

    def get_queryset(self):
        return super().get_queryset().exclude(student__isnull=False)

class UserImportView(BaseImportView):
    model = User
    fields = ['first_name', 'last_name', 'email', 'phone_number', 'is_professor', 'is_staff', 'faculties', 'programs', 'groups']

class UserCreateView(UserFormKwargsMixin, BaseCreateView):
    # this mixin will inject the user into the kwargs
    model = User
    form_class = UserForm

class UserUpdateView(UserCreateView, BaseUpdateView):
    pass

class UserDeleteView(BaseDeleteView):
    model = User

class StudentListView(BaseListView):
    model = Student
    table_fields = ['user.first_name', 'user.last_name', '_class', 'user.email', 'user.phone_number']
    object_actions = [
        ('✏️', 'users:change_student', None), 
        ('🗑️', 'users:delete_student', None), 
        ('score', 'academic:view_score', None)
    ]
    actions = [('+', 'users:add_student', None),
               ('import', 'users:import_student', 'users.add_student')]

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
            'phone_number': user.phone_number,
            'new_user': False,
        })
        return initial

class StudentDeleteView(BaseDeleteView):
    model = Student