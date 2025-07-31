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
    path('classes/change/<int:pk>/', views.ClassChangeView.as_view(), name='change_class'),
    path('classes/delete/<int:pk>/', views.ClassDeleteView.as_view(), name='delete_class'),
    # schedule
    path('schedules/', views.ScheduleListView.as_view(), name='view_schedule'),
    # score
    path('scores/<int:student_pk>', views.ScoreStudentListView.as_view(), name='view_score'),
    path('scores/add/<int:schedule_pk>/', views.ScoreScheduleEditView.as_view(), name='add_score'),
    # evaluation
    path('evaluations/', views.EvaluationListView.as_view(), name='view_evaluation'),
    path('evaluations/add/<int:schedule_pk>/', views.EvaluationCreateView.as_view(), name='add_evaluation'),
    path('evaluations/delete/', views.EvaluationBulkDeleteView.as_view(), name='delete_evaluation')
]
