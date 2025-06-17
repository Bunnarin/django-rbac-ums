from django.contrib import admin
from .models import ActivityTemplate
# Register your models here.

@admin.register(ActivityTemplate)
class ActivityTemplateAdmin(admin.ModelAdmin):
    list_display = ('name',)
    fields = ('name', 'template_json')
