from apps.core.views import BaseExportView, BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView
from .models import Course, Class, Schedule

class CourseListView(BaseListView):
    model = Course
    actions = ['add', 'change', 'delete']
    table_fields = ['name']
    group_by = ['faculty', 'program']

class CourseCreateView(BaseCreateView):
    model = Course

class CourseUpdateView(BaseUpdateView):
    model = Course

class CourseDeleteView(BaseDeleteView):
    model = Course

class ScheduleListView(BaseListView):
    model = Schedule
    actions = ['add', 'change', 'delete']
    table_fields = ['professor', 'course']
    group_by = ['faculty', 'program', '_class']

class ScheduleCreateView(BaseCreateView):
    model = Schedule
    
class ScheduleUpdateView(BaseUpdateView):
    """
    View for updating schedules with dynamic timeframe builder.
    """
    model = Schedule

class ScheduleDeleteView(BaseDeleteView):
    model = Schedule

class ScheduleExportView(BaseExportView):
    model = Schedule
    fields_to_export = ['faculty', 'program', 'professor', 'course', '_class', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

class ClassListView(BaseListView):
    model = Class
    actions = ['add', 'change', 'delete']
    table_fields = ['name', 'faculty', 'program']  # Include the fields for display
    group_by = ['faculty', 'program']  # Group by faculty first, then program

    def get_queryset(self):
        return super().get_queryset().select_related('faculty', 'program')

class ClassCreateView(BaseCreateView):
    model = Class

class ClassUpdateView(BaseUpdateView):
    model = Class

class ClassDeleteView(BaseDeleteView):
    model = Class
