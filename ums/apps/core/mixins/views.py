import json
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.forms import ValidationError

class ListViewPermissionMixin(PermissionRequiredMixin):
    def get_permission_required(self):
        """
        Dynamically determines the permission required based on the view's model.
        """
        if not hasattr(self, 'model') or not self.model:
            raise AttributeError(
                "AddViewPermissionMixin requires the view to have a 'model' attribute."
            )

        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name.lower()
        user = self.request.user
        for action in ["view", "change", "delete"]:
            if user.has_perm(f'{self.app_label}.{action}_{self.model_name}'):
                return [f'{self.app_label}.{action}_{self.model_name}']
        return [f'{self.app_label}.view_{self.model_name}'] # Default to view permission if no other permissions are found

class CreateViewPermissionMixin(PermissionRequiredMixin):
    """
    Mixin for views that require permission to add an object.
    Checks if the user has the 'add' permission for the model.
    """
    def get_permission_required(self):
        """
        Dynamically determines the permission required based on the view's model.
        """
        if not hasattr(self, 'model') or not self.model:
            raise AttributeError(
                "AddViewPermissionMixin requires the view to have a 'model' attribute."
            )

        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name.lower()
        return [f'{self.app_label}.add_{self.model_name}']

class UpdateViewPermissionMixin(PermissionRequiredMixin):
    """
    Mixin for views that require permission to add an object.
    Checks if the user has the 'add' permission for the model.
    """
    def get_permission_required(self):
        """
        Dynamically determines the permission required based on the view's model.
        """
        if not hasattr(self, 'model') or not self.model:
            raise AttributeError(
                "AddViewPermissionMixin requires the view to have a 'model' attribute."
            )

        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name.lower()
        return [f'{self.app_label}.change_{self.model_name}']

class DeleteViewPermissionMixin(PermissionRequiredMixin):
    """
    Mixin for views that require permission to add an object.
    Checks if the user has the 'add' permission for the model.
    """
    def get_permission_required(self):
        """
        Dynamically determines the permission required based on the view's model.
        """
        if not hasattr(self, 'model') or not self.model:
            raise AttributeError(
                "AddViewPermissionMixin requires the view to have a 'model' attribute."
            )

        self.app_label = self.model._meta.app_label
        self.model_name = self.model._meta.model_name.lower()
        return [f'{self.app_label}.delete_{self.model_name}']
