from django.views import View
from apps.core.views import BaseListView, BaseCreateView, BaseUpdateView, BaseDeleteView
from .models import Course, Class, Schedule, Score
from django.shortcuts import redirect
from django.forms import ModelForm, IntegerField
from django.db import transaction
from django.shortcuts import render

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

class ScoreBulkEditView(View):
    """
    View for bulk creating/updating scores for all students in a class.
    Handles both create and update operations using bulk_update_or_create.
    """
    template_name = 'core/generic_form.html'
    
    def create_form_class(self, students):
        """Create a dynamic form class with score fields for each student"""
        class ScoreBulkForm(ModelForm):
            def __init__(self, *args, **kwargs):
                existing_scores = kwargs.pop('existing_scores', {})
                super().__init__(*args, **kwargs)
                
                # Add score field for each student
                for student in students:
                    initial_value = existing_scores.get(student.id)
                    initial_score = initial_value.score if initial_value else 0
                    
                    self.fields[f'score_{student.id}'] = IntegerField(
                        label=f'{student.user.first_name} {student.user.last_name}',
                        min_value=0,
                        max_value=100,
                        initial=initial_score,
                    )
            
            class Meta:
                model = Score
                fields = []  # We'll add fields dynamically
        
        return ScoreBulkForm
    
    def get(self, request, *args, **kwargs):
        schedule = Schedule.objects.get(pk=self.kwargs['schedule_pk'])
        students = schedule._class.students.all()
        existing_scores = {
            score.student_id: score 
            for score in Score.objects.filter(student__in=students, course=schedule.course)
        }
        
        form_class = self.create_form_class(students)
        form = form_class(existing_scores=existing_scores)
        
        context = {
            'form': form,
            'title':f'Score for class: {schedule._class} course: {schedule.course}'
        }
        return render(request, self.template_name, context)
    
    @transaction.atomic
    def post(self, request, *args, **kwargs):       
        schedule = Schedule.objects.get(pk=self.kwargs['schedule_pk'])
        students = schedule._class.students.all()
        existing_scores = {
            score.student_id: score 
            for score in Score.objects.filter(student__in=students, course=schedule.course)
        }
        
        form_class = self.create_form_class(students)
        form = form_class(request.POST, existing_scores=existing_scores)
        
        if form.is_valid():
            # Prepare score objects for bulk operation
            score_objects = []
            for student in students:
                score_value = form.cleaned_data.get(f'score_{student.id}')
                # Only process if score is different from inital value
                if score_value != existing_scores.get(student.id):
                    score_objects.append(Score(
                        student=student,
                        course=schedule.course,
                        score=score_value
                    ))
            
            # Use bulk_update_or_create to handle both create and update
            if score_objects:
                Score.objects.bulk_update_or_create(
                    score_objects,
                    ['score'],  # Fields to update
                    match_field='student'  # Field to match on for updates
                )
            
            return redirect('academic:view_schedule')
        
        context = {
            'form': form,
            'title':f'Score for class: {schedule._class} course: {schedule.course}'
        }
        return render(request, self.template_name, context)
