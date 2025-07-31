from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views.generic import FormView
from django.urls import reverse_lazy
from django.db import transaction
from django.core.exceptions import ValidationError
from django.forms.models import modelform_factory, inlineformset_factory
from django_jsonform.widgets import JSONFormWidget
from apps.core.views import BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView, BaseBulkDeleteView, BaseImportView
from apps.core.forms import json_to_schema
from apps.organization.models import Faculty, Program
from apps.users.models import Student
from .models import Course, Class, Schedule, Score, Evaluation, EvalationTemplate
from .forms import create_score_form_class

class CourseListView(BaseListView):
    model = Course
    table_fields = ['name', 'year']
    object_actions = [('✏️', 'academic:change_course', None), 
    ('🗑️', 'academic:delete_course', None)]
    actions = [('+', 'academic:add_course', None)]

class CourseCreateView(BaseCreateView):
    model = Course

class CourseUpdateView(BaseUpdateView):
    model = Course

class CourseDeleteView(BaseDeleteView):
    model = Course

class ScheduleListView(BaseListView):
    model = Schedule
    object_actions = [('score', 'academic:add_score', None),
               ('evaluation', 'academic:add_evaluation', None)]
    table_fields = ['professor', 'course', 'course.year', '_class']

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
    permission_required = 'academic:add_score'
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
        Form = create_score_form_class(self.students, self.existing_scores)
        return Form(self.request.POST or None)
    
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
            if score_objects:
                Score.objects.bulk_update_or_create(
                    score_objects,
                    ['score'],  # Fields to update
                    match_field='student'  # Field to match on for updates
                )
            return super().form_valid(form)
        return super().form_invalid(form)

class EvaluationListView(BaseListView):
    model = Evaluation
    table_fields = ['schedule.course', 'schedule._class', 'schedule.professor', 'response']
    actions = [('clear all', 'academic:delete_evaluation', None)]

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
        Form = modelform_factory(Evaluation, fields=['response'], widgets={
            'response': JSONFormWidget(schema=json_to_schema(question_definition))
            })
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

class ClassListView(BaseListView):
    model = Class
    object_actions = [('✏️', 'academic:change_class', None),
               ('🗑️', 'academic:delete_class', None)]
    actions = [('+', 'academic:add_class', None)]
    table_fields = ['generation', 'name']

class ClassDeleteView(BaseDeleteView):
    model = Class

class ClassCreateView(BaseCreateView):
    model = Class
    fields = '__all__'
    success_url = reverse_lazy('academic:class_list')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        data['formset'] = inlineformset_factory(Class, Schedule, extra=1, can_delete=True, form=modelform_factory(
            Schedule, fields='__all__'))(self.request.POST or None)
        return data

    @transaction.atomic
    def form_valid(self, form):        
        # inject the faculty and program
        s = self.request.session
        
        if s['selected_faculty'] == "None": 
            form.instance.faculty = None
        else: 
            form.instance.faculty = Faculty.objects.get(pk=s['selected_faculty'])

        if s['selected_program'] == "None": 
            form.instance.program = None
        else: 
            form.instance.program = Program.objects.get(pk=s['selected_program'])
        
        # save changes
        context = self.get_context_data()
        formset = context['formset']
        if form.is_valid() and formset.is_valid():
            formset.instance = form.save()
            instances = formset.save(commit=False)
            for obj in formset.deleted_objects:
                obj.delete()
            for instance in instances:
                instance.save()
            return super().form_valid(form)
        elif not formset.is_valid():
            form.add_error(None,"schedules must be unique")
        return super().form_invalid(form)

class ClassUpdateView(ClassCreateView, BaseUpdateView):
    def get_context_data(self, **kwargs):
        data = super(BaseUpdateView, self).get_context_data(**kwargs)
        data['formset'] = inlineformset_factory(Class, Schedule, extra=1, can_delete=True, form=modelform_factory(
            Schedule, fields='__all__'))(self.request.POST or None, instance=self.object)
        return data
