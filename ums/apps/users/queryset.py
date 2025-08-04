from django.db import models
from django.db.models import Count, Q, F
from django.contrib.auth.models import Permission

class GroupQuerySet(models.QuerySet):    
    def for_user(self, user):
        """
        Returns groups where all permissions are a subset of the user's group permissions.
        """
        user_group_perm_ids = set(Permission.objects.filter(group__user=user).values_list('id', flat=True))
        
        return self.annotate(
            total_permissions=Count('permissions'),
            user_has_permissions=Count('permissions', filter=Q(permissions__id__in=user_group_perm_ids))
        ).filter(Q(total_permissions=0) | Q(total_permissions=F('user_has_permissions')))