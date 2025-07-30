from math import e
import os
import inspect
from django.conf import settings
from django.db import models
from django.core.exceptions import ImproperlyConfigured

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
    
    def _is_called_by_me(self):
        project_root = str(settings.PROJECT_DIR)
        caller_frame = inspect.currentframe().f_back.f_back
        caller_filepath = caller_frame.f_globals['__file__']
        absolute_caller_path = os.path.abspath(caller_filepath)
        return absolute_caller_path.startswith(project_root)

    def get_queryset(self, **kwargs):
        if 'request' in kwargs:
            request = kwargs.pop('request')
            if request is None:
                # explicitly not filter
                return super().get_queryset()
            else:
                return self._for_request(request)
        elif self._is_called_by_me():
            raise ImproperlyConfigured("missing request obj before querying")
        else: 
            # django called it, we let it pass
            return super().get_queryset()
        
    def _for_request(self, request):
        queryset = super().get_queryset()
        user = request.user
        s = request.session

        if any(perm in s['permissions'] for perm in ['access_global', 'access_faculty_wide', 'access_program_wide']):
            faculty_id = s.get('selected_faculty')
            program_id = s.get('selected_program')
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

        else:
            # we don't check if the model has the method or not, we do this to ensure that it's explicity defined
            q = self.model().get_user_rls_filter(user)
            return queryset.filter(q)