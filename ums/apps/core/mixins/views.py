from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.mixins import PermissionRequiredMixin


class ListViewPermissionMixin(AccessMixin):
    """
    Mixin for ListView that filters the queryset based on model permissions
    (view, change, or delete) for the current user.

    Requires the ListView to have a `model` attribute.
    Assumes your model manager has a `.for_user(user)` method to
    filter objects specific to a user's permissions/ownership.
    """
    permission_map = {
        'view': 'view',
        'change': 'change',
        'delete': 'delete',
    }

    def get_permission_model(self):
        if not hasattr(self, 'model') or self.model is None:
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} is missing the `model` attribute. "
                "Define `model` or override `get_permission_model()`."
            )
        return self.model

    def get_required_permissions_for_queryset(self):
        """
        Constructs the list of full permission strings (e.g., 'app_label.view_model_name')
        based on the `permission_map`.
        """
        model_obj = self.get_permission_model()
        app_label = model_obj._meta.app_label
        model_name = model_obj._meta.model_name

        permissions = []
        for action_prefix in self.permission_map.values():
            permissions.append(f"{app_label}.{action_prefix}_{model_name}")
        return permissions

    def get_queryset(self):
        """
        Overrides the default get_queryset to filter based on user permissions.
        """
        user = self.request.user
        model_to_filter = self.get_permission_model()

        if not user.is_authenticated:
            return model_to_filter.objects.none()

        required_perms = self.get_required_permissions_for_queryset()

        has_access = any(user.has_perm(perm) for perm in required_perms)

        if has_access:
            return model_to_filter.objects.for_user(user) # type: ignore
        else:
            return model_to_filter.objects.none()

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

        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name.lower()
        return [f'{app_label}.add_{model_name}']

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

        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name.lower()
        return [f'{app_label}.change_{model_name}']

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

        app_label = self.model._meta.app_label
        model_name = self.model._meta.model_name.lower()
        return [f'{app_label}.delete_{model_name}']
