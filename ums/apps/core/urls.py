from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('faculty/', views.set_faculty, name='set_faculty'),
    path('program/', views.set_program, name='set_program'),
    path('group/', views.set_group, name='set_group'),
]
