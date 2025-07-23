from django.contrib.auth.models import UserManager

class UserRLSManager(UserManager):
    """
    Custom manager that implements Row-Level Security (RLS) filtering.
    """

    def for_user(self, request):
        queryset = self.get_queryset()
        user = request.user

        faculty_id = request.session.get('selected_faculty')
        program_id = request.session.get('selected_program')

        if user.has_perm('users.access_global') or \
            user.has_perm('users.access_faculty_wide') or \
            user.has_perm('users.access_program_wide'):
            
            if faculty_id != "None":
                queryset = queryset.filter(faculties__pk=faculty_id)
            else:
                queryset = queryset.filter(faculties__isnull=True)

            if program_id != "None":
                queryset = queryset.filter(programs__pk=program_id)
            else:
                queryset = queryset.filter(programs__isnull=True)

            return queryset

        elif hasattr(self.model, 'get_user_rls_filter'):
            q = self.model().get_user_rls_filter(user)
            return queryset.filter(q)

        return queryset.none()