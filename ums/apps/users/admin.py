from django.contrib import admin
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.admin import UserAdmin
from django.db.models import Q
from allauth.account.models import EmailAddress
from .models import CustomUser
from .forms import CustomUserCreationForm

admin.site.unregister(Group)
@admin.register(Group)
class CustomGroupAdmin(admin.ModelAdmin):
    search_fields = ("name",)
    ordering = ("name",)
    filter_horizontal = ("permissions",)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
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

admin.site.unregister(EmailAddress)

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
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