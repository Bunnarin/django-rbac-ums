from django import forms
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

class RestrictedUserChangeForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get the current request user from the form's kwargs.
        # Django Admin's ModelAdmin.get_form passes the request via kwargs.
        # Ensure you handle the case where request might not be present (e.g., in tests).
        self.request = kwargs.pop('request', None)

        if self.request and not self.request.user.is_superuser:
            # Filter 'groups' field
            # A staff user can only assign groups they are already a member of.
            # Or, you might allow them to assign any groups that don't grant
            # permissions higher than their own. For simplicity, we'll assume
            # they can only assign groups they possess themselves.
            self.fields['groups'].queryset = self.request.user.groups.all()

            # Filter 'user_permissions' field
            # This is more complex: a staff user can only assign permissions
            # that they themselves possess.
            user_permissions_queryset = Permission.objects.none() # Start with an empty queryset

            # Get all permissions the current admin user has
            # This includes permissions from their groups and direct user_permissions
            all_user_perms_codenames = self.request.user.get_user_permissions() # Returns a set of 'app_label.codename' strings

            # Convert codenames back to Permission objects
            # Need to split 'app_label.codename' into app_label and codename
            # Then query ContentType and Permission
            q_objects = forms.Q()
            for perm_codename in all_user_perms_codenames:
                app_label, codename = perm_codename.split('.')
                q_objects |= forms.Q(content_type__app_label=app_label, codename=codename)
            
            # Filter the permissions queryset to only include permissions the current admin user has
            self.fields['user_permissions'].queryset = Permission.objects.filter(q_objects)

            # Optional: You might want to remove 'is_superuser' from fields if a non-superuser
            # shouldn't ever be able to grant superuser status.
            if 'is_superuser' in self.fields:
                self.fields['is_superuser'].widget = forms.HiddenInput()
                self.fields['is_superuser'].initial = False # Ensure it's not checked by default
                self.fields['is_superuser'].required = False # Not required if hidden
                # Alternatively, if you want to allow superusers to change it, but hide for others:
                # if not self.request.user.is_superuser:
                #     del self.fields['is_superuser']

class RestrictedUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.request = kwargs.pop('request', None)

        if self.request and not self.request.user.is_superuser:
            self.fields['groups'].queryset = self.request.user.groups.all()

            user_permissions_queryset = Permission.objects.none()
            all_user_perms_codenames = self.request.user.get_user_permissions()
            q_objects = forms.Q()
            for perm_codename in all_user_perms_codenames:
                app_label, codename = perm_codename.split('.')
                q_objects |= forms.Q(content_type__app_label=app_label, codename=codename)
            self.fields['user_permissions'].queryset = Permission.objects.filter(q_objects)

            if 'is_superuser' in self.fields:
                self.fields['is_superuser'].widget = forms.HiddenInput()
                self.fields['is_superuser'].initial = False
                self.fields['is_superuser'].required = False