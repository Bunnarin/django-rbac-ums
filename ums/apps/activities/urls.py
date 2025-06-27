from django.urls import path
from . import views

app_name = 'activities'

urlpatterns = [
    path('', views.ActivityListView.as_view(), name='view_activity'),
    path('create/templates/', views.ActivityTemplateSelectView.as_view(), name='add_activity'),
    path('create/<int:template_pk>/', views.ActivityCreateView.as_view(), name='submit_activity'),
    path('export/', views.ActivityExportView.as_view(), name='export_activity'),
]