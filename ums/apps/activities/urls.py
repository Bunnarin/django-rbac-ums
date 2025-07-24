from django.urls import path
from . import views

app_name = 'activities'

urlpatterns = [
    # activity
    path('', views.ActivityListView.as_view(), name='view_activity'),
    path('create/templates/', views.ActivityTemplateSelectView.as_view(), name='add_activity'),
    path('create/<int:template_pk>/', views.ActivityCreateView.as_view(), name='submit_activity'),
    path('delete/<int:pk>', views.ActivityDeleteView.as_view(), name='delete_activity'),
    path('delete/', views.ActivityBulkDeleteView.as_view(), name='delete_activity'),
    # activity template
    path('templates/', views.ActivityTemplateListView.as_view(), name='view_activitytemplate'),
    path('templates/create/', views.ActivityTemplateCreateView.as_view(), name='add_activitytemplate'),
    path('templates/change/<int:pk>/', views.ActivityTemplateUpdateView.as_view(), name='change_activitytemplate'),
    path('templates/delete/<int:pk>', views.ActivityTemplateDeleteView.as_view(), name='delete_activitytemplate'),
]