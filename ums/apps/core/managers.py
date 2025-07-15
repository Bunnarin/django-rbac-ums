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
            # Evaluate the many-to-many relationship to a list of IDs
            faculty_ids = list(user.faculties.values_list('id', flat=True))
            if not faculty_ids:  # If no faculties, return empty queryset
                return queryset.none()
            return queryset.filter(faculty_id__in=faculty_ids)

        if hasattr(self.model, 'program') and \
            user.has_perm('users.access_program_wide'):
            # Evaluate the many-to-many relationship to a list of IDs
            program_ids = list(user.programs.values_list('id', flat=True))
            if not program_ids:  # If no programs, return empty queryset
                return queryset.none()
            return queryset.filter(program_id__in=program_ids)

        if issubclass(self.model, UserRLSMixin):
            return queryset.filter(self.model().get_user_rls_filter(user))

        return queryset.none()