import json
from django.contrib.auth.mixins import AccessMixin
from django.core.exceptions import ImproperlyConfigured
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.forms import ValidationError

class ListViewPermissionMixin(AccessMixin):
    """
    Mixin for ListView that filters the queryset based on model permissions
    (view, change, or delete) for the current user.

    Requires the ListView to have a `model` attribute.
    Assumes your model manager has a `.for_user(user)` method to
    filter objects specific to a user's permissions/ownership.
    """
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
        self.app_label = model_obj._meta.app_label
        self.model_name = model_obj._meta.model_name

        permissions = []
        for action in ["view", "change", "delete"]: # if can change or delete, automatically can view
            permissions.append(f"{self.app_label}.{action}_{self.model_name}")
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

class TemplateBuilderMixin:
    """
    Mixin for Django Create/Update Views that handle dynamic JSON field creation
    via a frontend builder.

    It expects:
    - A hidden input field in the form with the name matching the `json_field_name_in_model`.
    - JavaScript on the frontend to populate this hidden input with a JSON string.
    """
    json_field_name_in_model = 'template_json' # Default field name in the model

    def form_valid(self, form):
        # Get the JSON string from the request.POST (from the hidden input field)
        template_json_str = self.request.POST.get(self.json_field_name_in_model)

        if template_json_str:
            try:
                # Parse the JSON string into a Python list/dict
                setattr(form.instance, self.json_field_name_in_model, json.loads(template_json_str))
            except json.JSONDecodeError:
                # Add a form error if the JSON is invalid
                form.add_error(None, ValidationError(f"Invalid JSON data provided for {self.json_field_name_in_model}."))
                return self.form_invalid(form)
        else:
            # If no JSON data, default to an empty list (or whatever your model default is)
            setattr(form.instance, self.json_field_name_in_model, [])

        return super().form_valid(form)
