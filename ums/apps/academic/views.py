from django.urls import reverse_lazy
from django.core.exceptions import ValidationError
from django.forms.models import modelform_factory
from django_jsonform.widgets import JSONFormWidget
from extra_views import InlineFormSetView
from apps.core.views import BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView, BaseBulkDeleteView, BaseWriteView
from apps.core.forms import json_to_schema
from .models import Course, Class, Schedule, Score, Evaluation, EvaluationTemplate
from .forms import create_score_form_class, ScheduleForm

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

class ScoreScheduleCreateView(BaseWriteView):
    """
    View for bulk creating/updating scores for all students in a class.
    """
    model = Score
    permission_required = [('add', 'score')]
    template_name = 'core/generic_form.html'
    success_url = reverse_lazy('academic:view_schedule')

    def get_form_class(self):
        Form = create_score_form_class(schedule_pk=self.kwargs['schedule_pk'])
        return Form
    
    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

class EvaluationListView(BaseListView):
    model = Evaluation
    table_fields = ['schedule.course', 'schedule._class', 'schedule.professor', 'response']
    actions = [('clear all', 'academic:delete_evaluation', None)]

class EvaluationCreateView(BaseWriteView):
    """
    View for creating/updating an evaluation for a schedule.
    """
    model = Evaluation
    success_url = reverse_lazy('academic:view_schedule')

    # throw an error if they've already created the evaluation
    def dispatch(self, request, *args, **kwargs):
        if Evaluation.objects.filter(schedule=kwargs['schedule_pk'], student__user=request.user).exists():
            raise ValidationError(f"You've already evaluated this schedule {kwargs['schedule_pk']}")
        return super().dispatch(request, *args, **kwargs)

    def get_form(self):
        question_definition = EvaluationTemplate.objects.get().question_definition
        Form = modelform_factory(Evaluation, fields=['response'], widgets={
            'response': JSONFormWidget(schema=json_to_schema(question_definition))
            })
        return super().get_form(form_class=Form)
    
    def form_valid(self, form):
        Evaluation.objects.create(
            schedule=Schedule.objects.get(pk=self.kwargs['schedule_pk']), 
            student=self.request.user.student, 
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

class ClassUpdateView(BaseWriteView, InlineFormSetView):
    model = Class
    inline_model = Schedule
    form_class = ScheduleForm
    factory_kwargs = {'extra': 1, 'can_delete': True}
    fields = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun', 'course', '_class']     
    success_url = reverse_lazy('academic:view_class')
    template_name = 'core/generic_form.html'
    permission_required = [('change', None)]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def formset_valid(self, formset):
        for data in formset.cleaned_data:
            if data.get('DELETE') == True:
                Schedule.objects.get(
                    course=data['course'], _class=data['_class'], professor=data['professor']
                ).delete()
        return super().formset_valid(formset)
