from django.db import models
from django.core.exceptions import ValidationError
from apps.core.managers import RLSManager
from .models import Faculty, Program

class OrganizationMixin(models.Model):
    """
    Abstract base class for models with both faculty and program affiliations.
    """
    faculty = models.ForeignKey(Faculty, on_delete=models.PROTECT)
    program = models.ForeignKey(Program, on_delete=models.PROTECT)
    objects = RLSManager()

    def clean(self):
        super().clean()
        if self.program and self.faculty and self.faculty != self.program.faculty:
            raise ValidationError({'program': 'The selected program does not belong to the assigned faculty.'})

    def save(self, *args, **kwargs):
        """
        Validate that the selected program belongs to the selected faculty.
        we do it in save and not clean because the form needs to inject affiliation after the clean
        """
        if self.faculty != self.program.faculty:
            raise ValidationError({'program': 'The selected program does not belong to the assigned faculty.'})
        super().save(*args, **kwargs)
    
    class Meta:
        abstract = True

class FacultyNullMixin(models.Model):
    """
    Abstract base class for models with an optional faculty affiliation.
    """
    faculty = models.ForeignKey(Faculty, null=True, blank=True, on_delete=models.SET_NULL)
    objects = RLSManager()

    class Meta:
        abstract = True

class ProgramNullMixin(models.Model):
    """
    Abstract base class for models with an optional program affiliation.
    """
    faculty = models.ForeignKey(Faculty, on_delete=models.PROTECT)
    program = models.ForeignKey(Program, null=True, blank=True, on_delete=models.SET_NULL)
    objects = RLSManager()

    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        if self.program and self.faculty and self.faculty != self.program.faculty:
            raise ValidationError({'program': 'The selected program does not belong to the assigned faculty.'})

class OrganizationsNullMixin(models.Model):
    """
    Abstract base class for models with optional multiple faculty and program affiliations.
    """
    faculties = models.ManyToManyField(Faculty, blank = True)
    programs = models.ManyToManyField(Program, blank = True)
    objects = RLSManager()

    class Meta:
        abstract = True
    
    def clean(self):
        super().clean()
        if not self.pk:
            # because we can't access manytomany field during creation. this logic have to be in the form
            return
        faculties = self.faculties.all()
        programs = self.programs.all()
        if faculties and programs:
            program_faculties = Faculty.objects.filter(
                program__in=programs
            ).distinct()
            missing_faculties = program_faculties.exclude(id__in=[f.id for f in faculties])
            if missing_faculties.exists():
                raise ValidationError({
                    'programs': f"The selected programs include faculties that are not in the assigned faculties: {', '.join(str(f) for f in missing_faculties)}"
                })