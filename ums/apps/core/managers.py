from django.db import models
from apps.core.mixins import UserRLSMixin

class RLSManager(models.Manager):
    """
    Custom manager that implements Row-Level Security (RLS) filtering.
    
    Usage:
        class MyModel(models.Model):
            objects = RLSManager()
        
        # Get filtered queryset for current user
        queryset = MyModel.objects.for_user(request)
    
    Security Levels:
        1. Superusers: Full access to all records
        2. Global access: Full access to all records (via 'users.access_global' permission)
        3. Faculty-wide access: Access to records within selected faculty (via 'users.access_faculty_wide')
        4. Program-wide access: Access to records within selected program (via 'users.access_program_wide')
        5. Row-level access: Custom filtering via UserRLSMixin
    """

    def for_user(self, request):
        """
        Get a queryset filtered by user permissions and context.
        
        Args:
            request: Django HTTP request object containing user and session information
            
        Returns:
            QuerySet: Filtered queryset based on user permissions and context
            
        Security Rules:
            - Superusers: Full access to all records
            - Global access: Full access to all records
            - Faculty access: Filtered by selected faculty (if user has faculty-wide permission)
            - Program access: Filtered by selected program (if user has program-wide permission)
            - Row-level: Filtered by model's get_user_rls_filter (if model inherits UserRLSMixin)
            - Default: Empty queryset if no matching permissions found
            
        Notes:
            - Validates that selected faculty/program belongs to user's faculties/programs
            - Returns empty queryset if invalid faculty/program ID is provided
            - Session keys used: 'selected_faculty' and 'selected_program'
        """
        queryset = self.get_queryset()
        user = request.user
        print(request.session.get('selected_faculty'))
        
        # Superusers have full access
        if user.is_superuser:
            return queryset

        # Apply the RLS filters based on the user's permissions
        if user.has_perm('users.access_global'):
            return queryset

        # Faculty-wide access check
        if hasattr(self.model, 'faculty') and user.has_perm('users.access_faculty_wide'):
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
            return queryset.none()

        # Program-wide access check
        if hasattr(self.model, 'program') and user.has_perm('users.access_program_wide'):
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
            return queryset.none()

        # Row-level security check (via UserRLSMixin)
        if issubclass(self.model, UserRLSMixin):
            return queryset.filter(self.model().get_user_rls_filter(user))

        return queryset.none()