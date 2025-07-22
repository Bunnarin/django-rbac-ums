from django.urls import path
from . import views

app_name = 'academic'

urlpatterns = [
    # course
    path('courses/', views.CourseListView.as_view(), name='view_course'),
    path('courses/create/', views.CourseCreateView.as_view(), name='add_course'),
    path('courses/change/<int:pk>/', views.CourseUpdateView.as_view(), name='change_course'),
    path('courses/delete/<int:pk>/', views.CourseDeleteView.as_view(), name='delete_course'),
    # class
    path('classes/', views.ClassListView.as_view(), name='view_class'),
    path('classes/create/', views.ClassCreateView.as_view(), name='add_class'),
    path('classes/change/<int:pk>/', views.ClassUpdateView.as_view(), name='change_class'),
    path('classes/delete/<int:pk>/', views.ClassDeleteView.as_view(), name='delete_class'),
    # course assignment
    path('schedules/', views.ScheduleListView.as_view(), name='view_schedule'),
    path('schedules/create/', views.ScheduleCreateView.as_view(), name='add_schedule'),
    path('schedules/change/<int:pk>/', views.ScheduleUpdateView.as_view(), name='change_schedule'),
    path('schedules/delete/<int:pk>/', views.ScheduleDeleteView.as_view(), name='delete_schedule'),
    # score
    path('scores/add/<int:schedule_pk>/', views.ScoreBulkEditView.as_view(), name='add_score'),
]
