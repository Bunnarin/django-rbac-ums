from apps.core.views import BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView
from .models import Course, Class, Schedule

class CourseListView(BaseListView):
    model = Course
    actions = ['add', 'change', 'delete']
    table_fields = ['name', 'faculty', 'program']

class CourseCreateView(BaseCreateView):
    model = Course

class CourseUpdateView(BaseUpdateView):
    model = Course

class CourseDeleteView(BaseDeleteView):
    model = Course

class ScheduleListView(BaseListView):
    model = Schedule
    actions = ['add', 'change', 'delete']
    table_fields = ['professor', 'course', '_class', 'faculty', 'program']

class ScheduleCreateView(BaseCreateView):
    model = Schedule
    
class ScheduleUpdateView(BaseUpdateView):
    """
    View for updating schedules with dynamic timeframe builder.
    """
    model = Schedule

class ScheduleDeleteView(BaseDeleteView):
    model = Schedule

class ClassListView(BaseListView):
    model = Class
    actions = ['add', 'change', 'delete']
    table_fields = ['name', 'faculty', 'program']

class ClassCreateView(BaseCreateView):
    model = Class

class ClassUpdateView(BaseUpdateView):
    model = Class

class ClassDeleteView(BaseDeleteView):
    model = Class
