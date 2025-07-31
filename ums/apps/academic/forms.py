from django import forms
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.academic.models import Score, Schedule
from apps.users.models import User

def create_score_form_class(students, existing_scores):
    class ScoreBulkCreateForm(forms.ModelForm):
        class Meta:
            model = Score
            fields = []  # We'll add fields dynamically

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            for student in students:
                self.fields[f'score_{student.id}'] = forms.IntegerField(
                    label=student,
                    min_value=0,
                    max_value=100,
                    initial=existing_scores.get(student.id).score,
                )
    return ScoreBulkCreateForm
    
class ScheduleForm(forms.ModelForm):
    # add the prof query field to get or create
    first_name = forms.CharField()
    last_name = forms.CharField()
    
    class Meta:
        model = Schedule
        fields = ['course', '_class', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']     

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # populate the first_name and last_name fields if have self.object
        if self.instance.pk:
            self.fields['first_name'].initial = self.instance.professor.first_name
            self.fields['last_name'].initial = self.instance.professor.last_name

    def clean(self):
        # check if the professor exists
        data = self.cleaned_data
        if not User.objects.filter(first_name=data['first_name'], last_name=data['last_name']).exists():
            raise ValidationError("Professor does not exist")

    def save(self, commit=True):
        data = self.cleaned_data
        prof = User.objects.get(first_name=data['first_name'], last_name=data['last_name'])
        schedule = super().save(commit=False)
        schedule.professor = prof
        if commit:
            schedule.save()
        return schedule