from django.db import models
from apps.core.mixins.models import UserRLSMixin

class RLSQuerySet(models.QuerySet):
    """
    A base QuerySet that applies Row-Level Security (RLS) filters based on
    organizational hierarchy and explicit permissions.
    Models using this QuerySet are expected to have 'faculty' and 'program'
    ForeignKeys or to override how they relate to Faculty/Program in RLS.
    """

    def for_user(self, user):
        if not user.is_authenticated:
            return self.none() # Anonymous users see nothing by default

        if user.is_superuser:
            return self # Superuser bypasses all RLS

        # --- Permission-based RLS Checks (Highest Priority) ---
        # 1. Global Access Check
        if user.has_perm('users.access_global'):
            return self # User with global access sees all

        # 2. Faculty-Wide Access Check
        if user.has_perm('users.access_faculty_wide'):
            if user.faculty:
                return self.filter(faculty=user.faculty)
            else:
                return self.none() # Perm but no assigned faculty

        # 3. Program-Wide Access Check
        if user.has_perm('users.access_program_wide'):
            if user.program:
                return self.filter(program=user.program)
            else:
                return self.none()

        # --- Default User-Specific RLS (Lowest Priority) ---
        elif issubclass(self.model, UserRLSMixin):
            return self.filter(self.model().get_user_rls_filter(user))

        else:
            return self.none() # Default to no access

class RLSManager(models.Manager):
    """
    A manager that uses RLSQuerySet to provide RLS-filtered query results.
    """

    def for_user(self, user):
        return RLSQuerySet(self.model, using=self._db).for_user(user)