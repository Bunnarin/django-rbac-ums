from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from apps.core.views import BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView
from braces.views import UserFormKwargsMixin
from .models import Student, CustomUser
from .forms import UserForm, StudentForm

class UserListView(BaseListView):
    model = CustomUser
    table_fields = ['first_name', 'last_name', 'email', 'phone_number', 'is_professor', 'is_staff']
    object_actions = [('✏️', 'users:change_customuser'), ('🗑️', 'users:delete_customuser')]
    actions = [('+', 'users:add_customuser')]

    def get_queryset(self):
        return super().get_queryset().exclude(student__isnull=False)

class UserCreateView(UserFormKwargsMixin, BaseCreateView):
    # this mixin will inject the user into the kwargs
    model = CustomUser
    form_class = UserForm

class UserUpdateView(UserCreateView, BaseUpdateView):
    pass

class UserDeleteView(BaseDeleteView):
    model = CustomUser

class StudentListView(BaseListView):
    model = Student
    table_fields = ['user.first_name', 'user.last_name', '_class', 'user.email', 'user.phone_number']
    object_actions = [
        ('✏️', 'users:change_student'), 
        ('🗑️', 'users:delete_student'), 
        ('score', 'academic:view_score')]
    actions = [('+', 'users:add_student')]

class StudentCreateView(BaseCreateView):
    model = Student
    form_class = StudentForm

    def form_valid(self, form):
        data = form.cleaned_data
        user_data = {
            'first_name': data['first_name'],
            'last_name': data['last_name'],
            'defaults': {
                'email': data['email'],
                'phone_number': data['phone_number']
            }
        }
        user, _ = CustomUser.objects.update_or_create(**user_data)
        student = form.save(commit=False)
        student.professor = user
        student.save()
        return super().form_valid(form)

class StudentUpdateView(StudentCreateView, BaseUpdateView):
    def get_initial(self):
        initial = super().get_initial()
        student = self.get_object()
        user = student.professor
        initial.update({
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'phone_number': user.phone_number,
        })
        return initial

class StudentDeleteView(BaseDeleteView):
    model = Student