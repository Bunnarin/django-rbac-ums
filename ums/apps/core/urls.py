from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('set-faculty/', views.set_faculty, name='set_faculty'),
    path('set-program/', views.set_program, name='set_program'),
]
