from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import FormView
from django.db import transaction
from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from apps.core.views import BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView
from apps.core.forms import get_json_form
from apps.users.models import Student, CustomUser
from .models import Course, Class, Schedule, Score, Evaluation, EvalationTemplate
from .forms import create_score_form_class

class CourseListView(BaseListView):
    model = Course
    table_fields = ['name']

class CourseCreateView(BaseCreateView):
    model = Course

class CourseUpdateView(BaseUpdateView):
    model = Course

class CourseDeleteView(BaseDeleteView):
    model = Course

class ScheduleListView(BaseListView):
    model = Schedule
    actions = [('score', 'academic:add_score'),
               ('evaluation', 'academic:add_evaluation')]
    table_fields = ['professor', 'course', '_class']

class ScheduleCreateView(BaseCreateView):
    model = Schedule

    def get_form(self):
        """
        Filter the professor queryset to exclude user with student profile to avoid bloat
        """
        form = super().get_form()
        form.fields['professor'].queryset = CustomUser.objects.exclude(student__isnull=False)
        return form
    
class ScheduleUpdateView(BaseUpdateView):
    """
    View for updating schedules with dynamic timeframe builder.
    """
    model = Schedule

class ScheduleDeleteView(BaseDeleteView):
    model = Schedule

class ClassListView(BaseListView):
    model = Class
    table_fields = ['generation', 'name']

class ClassCreateView(BaseCreateView):
    model = Class

class ClassUpdateView(BaseUpdateView):
    model = Class

class ClassDeleteView(BaseDeleteView):
    model = Class

class ScoreStudentListView(BaseListView):
    model = Score
    cruds = []
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
        self.schedule = Schedule.objects.select_related('course', '_class').get(pk=self.kwargs['schedule_pk'])
        self.students = self.schedule._class.student.all()
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

class EvaluationListView(BaseListView):
    model = Evaluation
    cruds = []
    table_fields = ['schedule', 'response']

class EvaluationEditView(PermissionRequiredMixin, FormView):
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
