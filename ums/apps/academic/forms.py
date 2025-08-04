from django import forms
from django.db import transaction
from apps.users.models import User
from .models import Score, Schedule, Course

def create_score_form_class(schedule_pk):
    schedule = Schedule.objects.select_related('course', '_class').get(pk=schedule_pk)
    students = schedule._class.students.all()
    existing_scores = {
        score.student_id: score.score 
        for score in Score.objects.filter(student__in=students, course=schedule.course)
    }

    class ScoreBulkCreateForm(forms.Form):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for student in students:
                self.fields[f'score_{student.id}'] = forms.IntegerField(
                    label=student,
                    min_value=0,
                    max_value=100,
                    initial=existing_scores.get(student.id, 0),
                )
        
        @transaction.atomic
        def save(self):
            data = self.cleaned_data
            score_objects = []
            for student in students:
                score_value = data.get(f'score_{student.id}')
                # Only process if score is different from inital value
                if score_value == existing_scores.get(student.id):
                    continue
                score_objects.append(
                    Score(
                        student=student,
                        course=schedule.course,
                        score=score_value
                    )
                )            
            if score_objects:
                Score.objects.bulk_update_or_create(
                    score_objects,
                    ['score'],  # Fields to update
                    match_field='student'  # Field to match on for updates
                )

    return ScoreBulkCreateForm
    
class ScheduleForm(forms.ModelForm):
    # add the prof query field to get or create
    first_name = forms.CharField()
    last_name = forms.CharField()
    email = forms.CharField(required=False, widget=forms.HiddenInput())
    
    class Meta:
        model = Schedule
        fields = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun', 'course', '_class']   

    def __init__(self, *args, request, **kwargs):
        super().__init__(*args, **kwargs)
        # filter the course choices based on the current affiliation
        self.fields['course'].queryset = Course.objects.get_queryset(request=request)
        # populate the first_name and last_name fields if have self.object
        if self.instance.pk:
            self.fields['first_name'].initial = self.instance.professor.first_name
            self.fields['last_name'].initial = self.instance.professor.last_name

    def clean(self):
        data = self.cleaned_data
        filters = {'first_name': data['first_name'], 'last_name': data['last_name']}
        if data.get('email'):
            filters['email'] = data['email']
        try:
            data['professor'] = User.objects.get(**filters)
        except User.DoesNotExist:
            self.add_error('first_name', f'Professor with this name does not exist')
        except User.MultipleObjectsReturned:
            # add an email field to filter the professor
            self.fields['email'].widget = forms.EmailInput()
            self.add_error('email', f'Multiple professors with the same name found. Please specify an email')

        return data

    def save(self, commit=True):
        data = self.cleaned_data
        self.instance = super().save(commit=False)
        self.instance.professor = data['professor']
        if commit:
            self.instance.save()
        return self.instance