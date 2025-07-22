from django.urls import reverse

class EditableMixin:
    def get_absolute_url(self):
        app_label = self._meta.app_label
        model_name = self._meta.model_name.lower()
        return reverse(f'{app_label}:change_{model_name}', kwargs={'pk': self.pk})