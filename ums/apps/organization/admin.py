from django.contrib import admin
from .models import Faculty, Program
# Register your models here.
@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'faculty',)
    list_filter = ('faculty',)
    search_fields = ('name', 'faculty__name',)
