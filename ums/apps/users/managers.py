from django.contrib.auth.models import UserManager
from apps.core.managers import RLSManager

class UserRLSManager(RLSManager, UserManager):
    """
    Custom manager that implements Row-Level Security (RLS) filtering.
    """

    def _for_request(self, request):
        queryset = super(UserManager, self).get_queryset()
        user = request.user

        if user.has_perm('users.access_global') or \
            user.has_perm('users.access_faculty_wide') or \
            user.has_perm('users.access_program_wide'):
            
            faculty_id = request.session.get('selected_faculty')
            program_id = request.session.get('selected_program')
            
            if faculty_id != "None":
                queryset = queryset.filter(faculties=faculty_id)
            else:
                queryset = queryset.filter(faculties__isnull=True)

            if program_id != "None":
                queryset = queryset.filter(programs=program_id)
            else:
                queryset = queryset.filter(programs__isnull=True)

            return queryset

        elif hasattr(self.model, 'get_user_rls_filter'):
            q = self.model().get_user_rls_filter(user)
            return queryset.filter(q)

        return queryset.none()