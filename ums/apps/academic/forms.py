from django.forms import ModelForm, IntegerField
from apps.academic.models import Score

def create_score_form_class(students):
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
                    label=student,
                    min_value=0,
                    max_value=100,
                    initial=initial_score,
                )
            
        class Meta:
            model = Score
            fields = []  # We'll add fields dynamically
    
    return ScoreBulkForm