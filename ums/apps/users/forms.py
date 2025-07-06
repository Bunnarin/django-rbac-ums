from django import forms
from django.contrib.auth import get_user_model
User = get_user_model()

class CustomUserCreationForm(forms.ModelForm):
    class Meta():
        model = User
        fields = ('email',)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_unusable_password()

        if commit:
            user.save()
        return user