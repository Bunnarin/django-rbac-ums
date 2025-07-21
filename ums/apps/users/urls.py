from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    # user
    path('', views.UserListView.as_view(), name='view_customuser'),
    path('create/', views.UserCreateView.as_view(), name='add_customuser'),
    path('change/<int:pk>/', views.UserUpdateView.as_view(), name='change_customuser'),
    path('delete/<int:pk>/', views.UserDeleteView.as_view(), name='delete_customuser'),
    # student
    path('students/', views.StudentListView.as_view(), name='view_student'),
    path('students/create/', views.StudentCreateView.as_view(), name='add_student'),
    path('students/change/<int:pk>/', views.StudentUpdateView.as_view(), name='change_student'),
    path('students/delete/<int:pk>/', views.StudentDeleteView.as_view(), name='delete_student'),
    # professor
    path('professors/', views.ProfessorListView.as_view(), name='view_professor'),
    path('professors/create/', views.ProfessorCreateView.as_view(), name='add_professor'),
    path('professors/change/<int:pk>/', views.ProfessorUpdateView.as_view(), name='change_professor'),
    path('professors/delete/<int:pk>/', views.ProfessorDeleteView.as_view(), name='delete_professor'),
]
