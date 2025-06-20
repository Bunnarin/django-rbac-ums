from django.db import models
from django.db.models import Q
from django.conf import settings # To get the AUTH_USER_MODEL
from apps.user_profile.models import Profile
from apps.core.mixins import UserRLSMixin

class RLSQuerySet(models.QuerySet):
    """
    A base QuerySet that applies Row-Level Security (RLS) filters based on
    organizational hierarchy and explicit permissions.
    Models using this QuerySet are expected to have 'faculty' and 'program'
    ForeignKeys or to override how they relate to Faculty/Program in RLS.
    """
    def _get_user_profile(self, user):
        try:
            return user.profile
        except Profile.DoesNotExist:
            return None

    def for_user(self, user):

        if not user.is_authenticated:
            return self.none() # Anonymous users see nothing by default

        if user.is_superuser:
            return self # Superuser bypasses all RLS

        user_profile = self._get_user_profile(user)
        if not user_profile:
            return self.none() # User has no profile, no data access

        # --- Permission-based RLS Checks (Highest Priority) ---
        # These are exclusive checks; if one returns, we're done.

        # 1. Global Access Check
        if user.has_perm('user_profile.access_global'):
            return self # User with global access sees all

        # 2. Faculty-Wide Access Check
        if user.has_perm('user_profile.access_faculty_wide'):
            if user_profile.faculty:
                return self.filter(faculty=user_profile.faculty)
            else:
                return self.none() # Perm but no assigned faculty

        # 3. Program-Wide Access Check
        if user.has_perm('user_profile.access_program_wide'):
            if user_profile.program:
                # User sees all activities within their assigned program
                # (assuming a direct program field on the model)
                return self.filter(program=user_profile.program)
            else:
                return self.none() # Perm but no assigned program

        # --- Default User-Specific RLS (Lowest Priority) ---
        elif issubclass(self.model, UserRLSMixin):
            pass
            # return self.filter(self.model().get_user_rls_filter(user))

        else:
            return self.none() # Default to no access

class RLSManager(models.Manager):
    """
    A manager that uses RLSQuerySet to provide RLS-filtered query results.
    """
    def get_queryset(self):
        return RLSQuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_queryset().for_user(user)