from django.contrib import admin
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.admin import UserAdmin
from django.db.models import Q
from allauth.account.models import EmailAddress
from .models import CustomUser
from .forms import CustomUserAdminForm

# Unregister default Group admin to replace with custom version
admin.site.unregister(Group)

@admin.register(Group)
class CustomGroupAdmin(admin.ModelAdmin):
    """  
    This admin class extends the default Group admin to provide:
    - Permission filtering based on user's own permissions
    - Extended permissions for users with faculty-wide or global access
    """
    search_fields = ("name",)
    ordering = ("name",)
    filter_horizontal = ("permissions",)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        """
        this just does some logic and modify the kwargs before passing it to the super
        """
        if db_field.name == "permissions":
            if request and not request.user.is_superuser:
                user = request.user
                user_perms_direct = user.user_permissions.all()
                user_perms_via_groups = Permission.objects.filter(group__in=user.groups.all())

                allowed_permissions_qs = (user_perms_direct | user_perms_via_groups).distinct()

                extended_permissions_qs = Permission.objects.filter(
                    Q(codename="access_faculty_wide") |
                    Q(codename="access_program_wide")
                ).distinct()

                if user.has_perm("users.access_global") or user.has_perm("users.access_faculty_wide"):
                    allowed_permissions_qs = (allowed_permissions_qs | extended_permissions_qs).distinct()

                kwargs["queryset"] = allowed_permissions_qs.select_related("content_type")
            else:
                kwargs["queryset"] = Permission.objects.all().select_related("content_type")

        return super().formfield_for_manytomany(db_field, request=request, **kwargs)

# Unregister default allauth email admin since we don't need it
admin.site.unregister(EmailAddress)

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Improved the defualt user admin to be cleaner and validate the affiliation
    """
    add_form = CustomUserAdminForm
    form = CustomUserAdminForm

    list_display = ('username', 'user_type',)
    list_filter = ('user_type', 'faculties','programs','groups','is_active')
    search_fields = ('email','username','first_name','last_name','phone_number')

    # tried moving this to the form logic but it doesn't work for some reason
    add_fieldsets = (
        ('Authentication', {'fields': ('username','email','phone_number')}),
        ('Personal Information', {'fields': ('first_name','last_name')}),
        ('Affiliations', {'fields': ('faculties','programs','user_type')}),
        ('Permissions', {'fields': ('is_active','is_staff','groups')}),
    )

    fieldsets = add_fieldsets
