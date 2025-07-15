from django.db import models
from apps.core.mixins import UserRLSMixin

class RLSManager(models.Manager):
    """
    A manager that uses RLSQuerySet to provide RLS-filtered query results.
    """
    def for_user(self, request):
        queryset = self.get_queryset()
        user = request.user
        print(request.session.get('selected_faculty'))
        if user.is_superuser:
            return queryset

        # Apply the RLS filters based on the user
        if user.has_perm('users.access_global'):
            return queryset

        if hasattr(self.model, 'faculty') and \
            user.has_perm('users.access_faculty_wide'):
            # Get selected faculty from session
            faculty_id = request.session.get('selected_faculty')
            if faculty_id:
                try:
                    faculty_id = int(faculty_id)
                    # Validate that the faculty is in user's faculties
                    if faculty_id in user.faculties.values_list('id', flat=True):
                        return queryset.filter(faculty_id=faculty_id)
                    return queryset.none()
                except (ValueError, TypeError):
                    return queryset.none()
            # If no faculty selected, return empty queryset
            return queryset.none()

        if hasattr(self.model, 'program') and \
            user.has_perm('users.access_program_wide'):
            # Get selected program from session
            program_id = request.session.get('selected_program')
            if program_id:
                try:
                    program_id = int(program_id)
                    # Validate that the program is in user's programs
                    if program_id in user.programs.values_list('id', flat=True):
                        return queryset.filter(program_id=program_id)
                    return queryset.none()
                except (ValueError, TypeError):
                    return queryset.none()
            # If no program selected, return empty queryset
            return queryset.none()

        if issubclass(self.model, UserRLSMixin):
            return queryset.filter(self.model().get_user_rls_filter(user))

        return queryset.none()