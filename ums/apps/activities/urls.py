from django.urls import path
from . import views

app_name = 'activities'

urlpatterns = [
    path('', views.ActivityListView.as_view(), name='activity-list'),
    path('create/templates/', views.ActivityTemplateSelectView.as_view(), name='activitytemplate-select'),
    path('create/<int:template_pk>/', views.ActivityCreateView.as_view(), name='activity-create'),
    path('export/', views.ActivityExportView.as_view(), name='activity-export'),
]