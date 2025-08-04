from django.contrib import admin
from django.contrib.auth.models import Group, Permission
from django.db.models import Q
from allauth.account.models import EmailAddress
from .queryset import GroupQuerySet

# Unregister default allauth email admin since we don't need it
admin.site.unregister(EmailAddress)

admin.site.unregister(Group)
@admin.register(Group)
class CustomGroupAdmin(admin.ModelAdmin):
    """  
    This admin class extends the default Group admin to provide:
    - Permission filtering based on user's own permissions to ensure SECURITY
    - Extended permissions for users with faculty-wide or global access
    """
    
    def get_queryset(self, request):
        return GroupQuerySet(Group).for_user(request.user)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        """
        this just does some logic and modify the kwargs before passing it to the super
        """
        if db_field.name == "permissions":
            if request and not request.user.is_superuser:
                user = request.user
                available_perms = Permission.objects.filter(group__in=user.groups.all()).distinct()

                if user.has_perm("users.access_global") or user.has_perm("users.access_faculty_wide"):
                    extended_permissions_qs = Permission.objects.filter(
                        Q(codename="access_faculty_wide") |
                        Q(codename="access_program_wide")
                    )
                    available_perms = (available_perms | extended_permissions_qs).distinct()

                kwargs["queryset"] = available_perms.select_related("content_type")
            else:
                kwargs["queryset"] = Permission.objects.all().select_related("content_type")

        return super().formfield_for_manytomany(db_field, request=request, **kwargs)
