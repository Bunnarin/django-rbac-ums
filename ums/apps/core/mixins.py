from django.urls import reverse

class DetailMixin:
    pass
    # def get_absolute_url(self):
    #     app_label = self._meta.app_label
    #     model_name = self._meta.model_name.lower()
    #     return reverse(f'{app_label}:view_{model_name}', kwargs={'pk': self.pk})