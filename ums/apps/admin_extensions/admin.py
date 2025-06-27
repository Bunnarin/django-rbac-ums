# apps/auth_extensions/admin.py
from django.contrib import admin
from django.contrib.auth.models import Group, Permission

# Unregister the default GroupAdmin if it's already registered
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass

@admin.register(Group)
class CustomGroupAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    ordering = ("name",)
    filter_horizontal = ("permissions",)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == "permissions":
            if request and not request.user.is_superuser:
                # Get permissions the current user has directly assigned
                user_perms_direct = request.user.user_permissions.all()

                # Get permissions from all groups the current user belongs to
                user_perms_via_groups = Permission.objects.filter(
                    group__in=request.user.groups.all()
                )

                # Combine and get distinct permissions
                # Use |= for Q objects or | for querysets (set union)
                allowed_permissions_qs = (user_perms_direct | user_perms_via_groups).distinct()

                # Set the queryset for the 'permissions' field
                # Apply select_related for performance on the final queryset
                kwargs["queryset"] = allowed_permissions_qs.select_related("content_type")
            else:
                # If it's a superuser, or no request (e.g., during tests), or field is not 'permissions'
                # ensure default behavior or full queryset is used.
                # It's also good to include the select_related for superusers too for consistency/perf.
                kwargs["queryset"] = Permission.objects.all().select_related("content_type")

        return super().formfield_for_manytomany(db_field, request=request, **kwargs)