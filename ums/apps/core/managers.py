from django.db import models

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
        if user.has_perm('users.access_global') :
            return queryset

        # Faculty-wide access check
        if user.has_perm('users.access_faculty_wide') and \
            (hasattr(self.model, 'faculty') or hasattr(self.model, 'faculties')):
            user_faculty_id = request.session.get('selected_faculty')
            return queryset.filter(faculty_id=user_faculty_id)

        # Program-wide access check
        if user.has_perm('users.access_program_wide') and \
            (hasattr(self.model, 'program') or hasattr(self.model, 'programs')):
            user_program_id = request.session.get('selected_program')
            return queryset.filter(program_id=user_program_id)

        if hasattr(self.model, 'get_user_rls_filter'):
            return queryset.filter(self.model().get_user_rls_filter(user))

        return queryset.none()