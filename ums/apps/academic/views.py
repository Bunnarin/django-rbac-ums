from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import FormView
from django.db import transaction
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from apps.core.views import BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView, BaseBulkDeleteView
from apps.core.forms import get_json_form
from apps.users.models import Student
from .models import Course, Class, Schedule, Score, Evaluation, EvalationTemplate
from .forms import create_score_form_class, ScheduleForm

class CourseListView(BaseListView):
    model = Course
    table_fields = ['name', 'year']
    object_actions = [('✏️', 'academic:change_course'), ('🗑️', 'academic:delete_course')]
    actions = [('+', 'academic:add_course')]

class CourseCreateView(BaseCreateView):
    model = Course

class CourseUpdateView(BaseUpdateView):
    model = Course

class CourseDeleteView(BaseDeleteView):
    model = Course

class ScheduleListView(BaseListView):
    model = Schedule
    object_actions = [('score', 'academic:add_score'),
               ('evaluation', 'academic:add_evaluation'),
               ('✏️', 'academic:change_schedule'),
               ('🗑️', 'academic:delete_schedule')]
    actions = [('+', 'academic:add_schedule')]
    table_fields = ['professor', 'course', 'course.year', '_class']

class ScheduleCreateView(BaseCreateView):
    model = Schedule
    form_class = ScheduleForm
    
class ScheduleUpdateView(ScheduleCreateView, BaseUpdateView):
    """
    View for updating schedules with dynamic timeframe builder.
    """
    def get_initial(self):
        initial = super().get_initial()
        student = self.get_object()
        prof = student.professor
        initial.update({
            'first_name': prof.first_name,
            'last_name': prof.last_name,
        })
        return initial

class ScheduleDeleteView(BaseDeleteView):
    model = Schedule

class ClassListView(BaseListView):
    model = Class
    object_actions = [('✏️', 'academic:change_class'),
               ('🗑️', 'academic:delete_class')]
    actions = [('+', 'academic:add_class')]
    table_fields = ['generation', 'name']

class ClassCreateView(BaseCreateView):
    model = Class

class ClassUpdateView(BaseUpdateView):
    model = Class

class ClassDeleteView(BaseDeleteView):
    model = Class

class ScoreStudentListView(BaseListView):
    model = Score
    table_fields = ['course', 'score']

    def get_queryset(self):
        return Score.objects.filter(student_id=self.kwargs['student_pk']).select_related('course')

class ScoreScheduleEditView(PermissionRequiredMixin, FormView):
    """
    View for bulk creating/updating scores for all students in a class.
    """
    template_name = 'core/generic_form.html'
    permission_required = 'academic.add_score'
    success_url = reverse_lazy('academic:view_schedule')

    def get_form(self):
        self.schedule = Schedule.objects.select_related(
            'course', '_class').get(pk=self.kwargs['schedule_pk'])
        self.students = self.schedule._class.students.all()
        self.existing_scores = {
            score.student_id: score 
            for score in Score.objects.filter(
                student__in=self.students, course=self.schedule.course
                )
        }
        Form = create_score_form_class(self.students)
        return Form(self.request.POST or None, existing_scores=self.existing_scores)
    
    @transaction.atomic
    def form_valid(self, form):
        if form.is_valid():
            score_objects = []
            for student in self.students:
                score_value = form.cleaned_data.get(f'score_{student.id}')
                # Only process if score is different from inital value
                if score_value == self.existing_scores.get(student.id):
                    continue
                score_objects.append(
                    Score(
                        student=student,
                        course=self.schedule.course,
                        score=score_value
                    )
                )            
            # Use bulk_update_or_create to handle both create and update
            if score_objects:
                Score.objects.bulk_update_or_create(
                    score_objects,
                    ['score'],  # Fields to update
                    match_field='student'  # Field to match on for updates
                )
        return super().form_valid(form)

class EvaluationListView(BaseListView):
    model = Evaluation
    table_fields = ['schedule.course', 'schedule._class', 'schedule.professor', 'response']
    actions = [('clear all', 'academic:delete_evaluation')]

class EvaluationCreateView(PermissionRequiredMixin, FormView):
    """
    View for creating/updating an evaluation for a schedule.
    """
    template_name = 'core/generic_form.html'
    permission_required = 'academic.add_evaluation'
    success_url = reverse_lazy('academic:view_schedule')

    # throw an error if they've already created the evaluation
    def dispatch(self, request, *args, **kwargs):
        if Evaluation.objects.filter(schedule=kwargs['schedule_pk'], student__user=request.user).exists():
            raise ValidationError("You've already evaluated this schedule")
        return super().dispatch(request, *args, **kwargs)

    def get_form(self):
        question_definition = EvalationTemplate.objects.get().question_definition
        Form = get_json_form(question_definition, Evaluation, ['response'], 'response')
        return super().get_form(form_class=Form)
    
    def form_valid(self, form):
        if form.is_valid():
            schedule = Schedule.objects.select_related('_class').get(pk=self.kwargs['schedule_pk'])
            Evaluation.objects.create(
                schedule=schedule, 
                student=Student.objects.get(user=self.request.user, _class=schedule._class), 
                response=form.cleaned_data['response']
                )
        return super().form_valid(form)

class EvaluationBulkDeleteView(BaseBulkDeleteView):
    """
    delete everything
    """
    model = Evaluation
