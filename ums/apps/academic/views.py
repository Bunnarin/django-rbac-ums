from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import FormView
from django.db import transaction
from django.urls import reverse_lazy
from apps.core.views import BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView
from .models import Course, Class, Schedule, Score
from .forms import create_score_form_class


class CourseListView(BaseListView):
    model = Course
    table_fields = ['name', 'faculty', 'program']

class CourseCreateView(BaseCreateView):
    model = Course

class CourseUpdateView(BaseUpdateView):
    model = Course

class CourseDeleteView(BaseDeleteView):
    model = Course

class ScheduleListView(BaseListView):
    model = Schedule
    actions = [('score', 'academic:add_score')]
    table_fields = ['professor', 'course', '_class']

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
    table_fields = ['name', 'faculty', 'program']

class ClassCreateView(BaseCreateView):
    model = Class
    fields = ['faculty', 'program', 'name']

class ClassUpdateView(BaseUpdateView):
    model = Class

class ClassDeleteView(BaseDeleteView):
    model = Class

class ScoreBulkEditView(PermissionRequiredMixin, FormView):
    """
    View for bulk creating/updating scores for all students in a class.
    """
    template_name = 'core/generic_form.html'
    permission_required = 'academic.add_score'
    success_url = reverse_lazy('academic:view_schedule')

    def get_form(self):
        self.schedule = Schedule.objects.select_related('course', '_class').get(pk=self.kwargs['schedule_pk'])
        self.students = self.schedule._class.students.all()
        self.existing_scores = {
            score.student_id: score 
            for score in Score.objects.filter(
                student__in=self.students, course=self.schedule.course
                )
        }
        form_class = create_score_form_class(self.students)
        form = form_class(self.request.POST or None, existing_scores=self.existing_scores)
        return form
    
    @transaction.atomic
    def form_valid(self, form):
        if form.is_valid():
            score_objects = []
            for student in self.students:
                score_value = form.cleaned_data.get(f'score_{student.id}')
                # Only process if score is different from inital value
                if score_value == self.existing_scores.get(student.id):
                    continue
                score_objects.append(Score(
                    student=student,
                    course=self.schedule.course,
                    score=score_value
                ))
            
            # Use bulk_update_or_create to handle both create and update
            if score_objects:
                Score.objects.bulk_update_or_create(
                    score_objects,
                    ['score'],  # Fields to update
                    match_field='student'  # Field to match on for updates
                )
        return super().form_valid(form)
