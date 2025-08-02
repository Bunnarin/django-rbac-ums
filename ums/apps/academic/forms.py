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
        # manually inject the schedule if because the formset won't do it for some reason
        schedule, _ = Schedule.objects.get_or_create(_class=data['_class'], course=data['course'], professor=data['professor'])
        data['id'] = schedule.id
        print(schedule.id)
        return data

    def save(self, commit=True):
        data = self.cleaned_data
        self.instance = self.save(commit=False)
        self.instance.professor = data['professor']
        if commit:
            self.instance.save()
        return self.instance