from django.db import models

class RLSManager(models.Manager):
    """
    Custom manager that implements Row-Level Security (RLS) filtering.
    requires the model to possess both faculty and program period.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the manager with the field that has affiliation.
        example: schedule has no direct affiliation but its course field does
        """
        self.field_with_affiliation = kwargs.pop('field_with_affiliation', "")
        if self.field_with_affiliation != "":
            self.field_with_affiliation += "__"
            self.field_with_affiliation = self.field_with_affiliation.replace('.', '__')
        super().__init__(*args, **kwargs)
    
    def for_user(self, request):
        queryset = self.get_queryset()
        user = request.user
        s = request.session
        faculty_id = s.get('selected_faculty')
        program_id = s.get('selected_program')

        if user.has_perm('users.access_global') or \
            user.has_perm('users.access_faculty_wide') or \
            user.has_perm('users.access_program_wide'):
            filters = {}
            if faculty_id != "None":
                filters[f"{self.field_with_affiliation}faculty"] = faculty_id
            else:
                filters[f"{self.field_with_affiliation}faculty__isnull"] = True

            if program_id != "None":
                filters[f"{self.field_with_affiliation}program"] = program_id
            else:
                filters[f"{self.field_with_affiliation}program__isnull"] = True

            return queryset.filter(**filters)

        elif hasattr(self.model, 'get_user_rls_filter'):
            q = self.model().get_user_rls_filter(user)
            return queryset.filter(q)

        return queryset.none()