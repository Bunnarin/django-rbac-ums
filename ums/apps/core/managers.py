from django.db import models
from apps.core.mixins import UserRLSMixin

class RLSManager(models.Manager):
    """
    A manager that uses RLSQuerySet to provide RLS-filtered query results.
    """
    def for_user(self, user):
        queryset = self.get_queryset()

        if user.is_superuser:
            return queryset

        # Apply the RLS filters based on the user
        if user.has_perm('users.access_global'):
            return queryset

        if hasattr(self.model, 'faculty') and \
            user.has_perm('users.access_faculty_wide'):
            return queryset.filter(faculty=user.faculty)

        if hasattr(self.model, 'program') and \
            user.has_perm('users.access_program_wide'):
            return queryset.filter(program=user.program)

        if issubclass(self.model, UserRLSMixin):
            return queryset.filter(self.model().get_user_rls_filter(user))

        return queryset.none()