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