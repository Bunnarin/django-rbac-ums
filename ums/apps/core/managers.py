from django.db import models
from apps.core.mixins import UserRLSMixin

class RLSManager(models.Manager):
    """
    Custom manager that implements Row-Level Security (RLS) filtering.
    """

    def for_user(self, request):
        queryset = self.get_queryset()
        user = request.user
        
        # Superusers have full access
        if user.is_superuser:
            return queryset

        # Apply the RLS filters based on the user's permissions
        if user.has_perm('users.access_global'):
            return queryset

        # Faculty-wide access check
        if hasattr(self.model, 'faculty') and user.has_perm('users.access_faculty_wide'):
            faculty_id = request.session.get('selected_faculty')
            return queryset.filter(faculty_id=faculty_id)

        # Program-wide access check
        if hasattr(self.model, 'program') and user.has_perm('users.access_program_wide'):
            program_id = request.session.get('selected_program')
            return queryset.filter(program_id=program_id)

        # Row-level security check (via UserRLSMixin)
        if issubclass(self.model, UserRLSMixin):
            return queryset.filter(self.model().get_user_rls_filter(user))

        return queryset.none()