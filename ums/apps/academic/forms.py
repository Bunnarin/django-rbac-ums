from django import forms
from apps.academic.models import Score, Schedule, Course
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
        fields = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'course']   

    def __init__(self, *args, request, **kwargs):
        self.fields['first_name'] = forms.CharField()
        self.fields['last_name'] = forms.CharField()
        super().__init__(*args, **kwargs)
        # filter the course choices based on the current affiliation
        self.fields['course'].queryset = Course.objects.get_queryset(request=request)
        # populate the first_name and last_name fields if have self.object
        if self.instance.pk:
            self.fields['first_name'].initial = self.instance.professor.first_name
            self.fields['last_name'].initial = self.instance.professor.last_name

    def clean(self):
        data = self.cleaned_data
        if not User.objects.filter(first_name=data['first_name'], last_name=data['last_name']).exists():
            self.add_error('first_name', f'Professor with the name {data["first_name"]} {data["last_name"]} does not exist')

    def save(self, commit=True):
        data = self.cleaned_data
        schedule = super().save(commit=False)
        prof = User.objects.get(first_name=data['first_name'], last_name=data['last_name'])
        schedule.professor = prof
        if commit:
            schedule.save()
        return schedule