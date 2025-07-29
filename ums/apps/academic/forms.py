from django import forms
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.academic.models import Score, Schedule
from apps.users.models import User

class ScoreBulkCreateForm(forms.ModelForm):
    class Meta:
        model = Score
        fields = []  # We'll add fields dynamically

    def __init__(self, *args, **kwargs):
        self.students = kwargs.pop('students', {})
        self.existing_scores = kwargs.pop('existing_scores', {})
        self.schedule = kwargs.pop('schedule', {})
        super().__init__(*args, **kwargs)
        
        # Add score field for each student
        for student in self.students:
            initial_score = self.existing_scores.get(student.id) or 0
            # initial_score = initial_value.score if initial_value else 0
            self.fields[f'score_{student.id}'] = forms.IntegerField(
                label=student,
                min_value=0,
                max_value=100,
                initial=initial_score,
            )
    
    @transaction.atomic
    def save(self):
        score_objects = []
        for student in self.students:
            score_value = self.cleaned_data.get(f'score_{student.id}')
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
    
class ScheduleForm(forms.ModelForm):
    # add the prof query field to get or create
    first_name = forms.CharField()
    last_name = forms.CharField()
    new_user = forms.BooleanField(required=False)
    selected_user = forms.ChoiceField(required=False, disabled=True)
    
    class Meta:
        model = Schedule
        fields = ['course', '_class', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    
    def clean(self):
        """
        this is to ensure the user does not typo name and to confirm their intention
        """
        data = super().clean()
        exist = User.objects.filter(first_name=data['first_name'], last_name=data['last_name']).exists()
        if exist and data['new_user']:
            duplicated_users = User.objects.filter(first_name=data['first_name'], last_name=data['last_name'])
            self.fields['selected_user'].choices = [(user.id, f"{user.email} {user.phone_number}") for user in duplicated_users]
            self.fields['selected_user'].disabled = False
            raise ValidationError({"new_user": "User already exists. please check name spelling OR uncheck THIS and select an existing user instead"})
        elif not exist and not data['new_user']:
            raise ValidationError({"new_user": "User does not exist. please check name spelling OR check THIS to create this user instead"})
        
        return data        

    def save(self, commit=True):
        data = self.cleaned_data
        if data['new_user']:
            prof = User.objects.create(first_name=data['first_name'], last_name=data['last_name'])
        else:
            prof = User.objects.get(pk=data['selected_user'])

        schedule = super().save(commit=False)
        schedule.professor = prof
        if commit:
            schedule.save()
        return schedule