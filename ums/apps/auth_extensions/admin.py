# auth_extensions/admin.py (or your_app_name/admin.py)

from django.contrib import admin
from django.contrib.auth.models import Group, Permission # Import Group and Permission models
from django.db.models import Q # Needed for combining querysets if you want to be super explicit (though | works fine)

admin.site.unregister(Group)

@admin.register(Group)
class CustomGroupAdmin(admin.ModelAdmin):
    # Copy the original attributes from Django's GroupAdmin for consistent behavior
    search_fields = ("name",)
    ordering = ("name",)
    filter_horizontal = ("permissions",) # This keeps the nice dual-pane selector

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        """
        Overrides the default method to restrict permissions based on the requesting user.
        """
        if db_field.name == "permissions":
            # Original Django logic for performance
            qs = kwargs.get("queryset", db_field.remote_field.model.objects)
            kwargs["queryset"] = qs.select_related("content_type")

            # === YOUR CUSTOM LOGIC STARTS HERE ===
            if request and not request.user.is_superuser:
                user_permissions_queryset = Permission.objects.none()
                user_permissions_queryset |= request.user.user_permissions.all()
                user_permissions_queryset |= Permission.objects.filter(
                    group__in=request.user.groups.all()
                )
                allowed_permissions = user_permissions_queryset.distinct()
                kwargs["queryset"] = allowed_permissions.select_related("content_type")

        return super().formfield_for_manytomany(db_field, request=request, **kwargs)