from django.contrib import admin
from .models import EvalationTemplate

@admin.register(EvalationTemplate)
class EvalationTemplateAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False
        
    def has_delete_permission(self, request, obj=None):
        return False
    
