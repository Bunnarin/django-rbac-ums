from django.urls import path
from .views import ActivityTemplateListView, ActivityListView, ActivityCreateView

app_name = 'activities'

urlpatterns = [
    path('', ActivityListView.as_view(), name='activity-list'),
    path('create', ActivityTemplateListView.as_view(), name='create'),
    path('submit/<int:template_pk>', ActivityCreateView.as_view(), name='submit'),
]