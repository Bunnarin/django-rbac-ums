from django.contrib import admin
from .models import Profile

# Register your models here.
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'faculty', 'program',)
    list_filter = ('faculty', 'program',)
    search_fields = ('user__username',)
    raw_id_fields = ('user', 'faculty',) # Use raw_id_fields for FKs for better UX/performance

    # --- Crucial: Disable Add and Delete permissions ---
    def has_add_permission(self, request):
        return False # Users cannot add new UserProfiles through the admin

    def has_delete_permission(self, request, obj=None):
        return False # Users cannot delete UserProfiles through the admin