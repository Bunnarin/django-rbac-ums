from django.contrib import admin
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.admin import UserAdmin
from django.db.models import Q
from allauth.account.models import EmailAddress
from .models import CustomUser
from .forms import CustomUserCreationForm

# Unregister default Group admin to replace with custom version
admin.site.unregister(Group)

@admin.register(Group)
class CustomGroupAdmin(admin.ModelAdmin):
    """  
    This admin class extends the default Group admin to provide:
    - Permission filtering based on user's own permissions
    - Extended permissions for users with faculty-wide or global access
    - Proper permission organization in the admin interface
    """
    search_fields = ("name",)
    ordering = ("name",)
    filter_horizontal = ("permissions",)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        """
        Override the form field for many-to-many relationships.
        
        For the permissions field, filters the available permissions based on:
        - Superuser: All permissions
        - Regular user: Only permissions they have directly or via groups
        - Users with faculty-wide/global access: Additional faculty/program permissions
        
        Args:
            db_field: The database field being rendered
            request: The current HTTP request
            **kwargs: Additional keyword arguments
            
        Returns:
            The modified form field with filtered queryset
        """
        if db_field.name == "permissions":
            if request and not request.user.is_superuser:
                user = request.user
                user_perms_direct = user.user_permissions.all()
                user_perms_via_groups = Permission.objects.filter(group__in=user.groups.all())

                allowed_permissions_qs = (user_perms_direct | user_perms_via_groups).distinct()

                extended_permissions_qs = Permission.objects.filter(
                    Q(content_type__app_label='users', codename="access_faculty_wide") |
                    Q(content_type__app_label='users', codename="access_program_wide")
                ).distinct()

                if user.has_perm("users.access_global") or user.has_perm("users.access_faculty_wide"):
                    allowed_permissions_qs = (allowed_permissions_qs | extended_permissions_qs).distinct()

                kwargs["queryset"] = allowed_permissions_qs.select_related("content_type")
            else:
                kwargs["queryset"] = Permission.objects.all().select_related("content_type")

        return super().formfield_for_manytomany(db_field, request=request, **kwargs)

# Unregister default EmailAddress admin since we don't need it
admin.site.unregister(EmailAddress)

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Custom admin class for managing users with faculty and program affiliations.
    
    This admin class extends Django's UserAdmin to provide:
    - Custom form for user creation
    - Custom fieldsets for user management
    - Search and filter capabilities
    - Faculty and program affiliation management
    
    Fieldsets:
        Basic Info: username, email, phone_number
        Affiliations: faculties, programs
        Permissions: is_active, is_staff, groups
    """
    add_form = CustomUserCreationForm

    list_display = ('username', 'is_staff',)
    list_filter = ('is_staff', 'groups',)
    search_fields = ('email','username',)

    add_fieldsets = (
        (None, {'fields': ('username','email','phone_number'),}),
        ('Affiliations', {'fields': ('faculties','programs',),}),
        ('Permissions', {'fields': ('is_active','is_staff','groups',),}),
    )

    fieldsets = (
        (None, {'fields': ('username','email','phone_number'),}),
        ('Affiliations', {'fields': ('faculties','programs',),}),
        ('Permissions', {'fields': ('is_active','is_staff','groups',),}),
    )