from django.contrib.auth.models import UserManager
from apps.core.managers import RLSManager

class UserRLSManager(RLSManager, UserManager):
    """
    Custom manager that implements Row-Level Security (RLS) filtering.
    """

    def _for_request(self, request):
        queryset = super(UserManager, self).get_queryset()
        user = request.user
        s = request.session

        if any(perm in s['permissions'] for perm in ['access_global', 'access_faculty_wide', 'access_program_wide']):
            faculty_id = s.get('selected_faculty')
            program_id = s.get('selected_program')
            
            if faculty_id != "None":
                queryset = queryset.filter(faculties=faculty_id)
            else:
                queryset = queryset.filter(faculties__isnull=True)

            if program_id != "None":
                queryset = queryset.filter(programs=program_id)
            else:
                queryset = queryset.filter(programs__isnull=True)

            return queryset

        else:
            # we don't check if the model has the method or not, we do this to ensure that it's explicity defined
            q = self.model().get_user_rls_filter(user)
            return queryset.filter(q)