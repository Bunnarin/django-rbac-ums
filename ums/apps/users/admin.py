from django.contrib import admin
from django.contrib.auth.models import Group, Permission
from django.db.models import Q
from allauth.account.models import EmailAddress
from .models import User

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
    search_fields = ("name",)
    ordering = ("name",)
    filter_horizontal = ("permissions",)

    def get_change_permissions(self, request):
        if request.user.is_superuser:
            return True
        return False
        
    def get_delete_permission(self, request):
        if request.user.is_superuser:
            return True
        return False

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        """
        this just does some logic and modify the kwargs before passing it to the super
        """
        if db_field.name == "permissions":
            if request and not request.user.is_superuser:
                user = request.user
                user_perms_via_groups = Permission.objects.filter(group__in=user.groups.all()).distinct()

                extended_permissions_qs = Permission.objects.filter(
                    Q(codename="access_faculty_wide") |
                    Q(codename="access_program_wide")
                ).distinct()

                if any(perm for perm in request.session['permissions'] if perm in ["access_global", "access_faculty_wide"]):
                    user_perms_via_groups = (user_perms_via_groups | extended_permissions_qs).distinct()

                kwargs["queryset"] = user_perms_via_groups.select_related("content_type")
            else:
                kwargs["queryset"] = Permission.objects.all().select_related("content_type")

        return super().formfield_for_manytomany(db_field, request=request, **kwargs)
