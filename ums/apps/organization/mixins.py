from django.db import models
from django.core.exceptions import ValidationError
from .models import Faculty, Program

class OrganizationMixin(models.Model):
    """
    Abstract base class for models that require both faculty and program relationships.
    """
    faculty = models.ForeignKey(Faculty, on_delete=models.PROTECT,)
    program = models.ForeignKey(Program, on_delete=models.PROTECT,)

    def clean(self):
        """
        Validate that the selected program belongs to the selected faculty.
        """
        super().clean()
        if self.faculty != self.program.faculty:
            raise ValidationError({'program': 'The selected program does not belong to the assigned faculty.'})
    
    class Meta:
        abstract = True

class OrganizationNullMixin(models.Model):
    """
    Abstract base class for models that require optional faculty and program relationships.
    """
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    program = models.ForeignKey(
        Program,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def clean(self):
        """
        Validate that the selected program belongs to the selected faculty.
        """
        super().clean()
        if self.program and self.faculty:
            if self.faculty != self.program.faculty:
                raise ValidationError({'program': 'The selected program does not belong to the assigned faculty.'})
    
    class Meta:
        abstract = True

class FacultyMixin(models.Model):
    """
    Abstract base class for models that require a faculty relationship.
    """
    faculty = models.ForeignKey(Faculty, on_delete=models.PROTECT)

    class Meta:
        abstract = True

class FacultyNullMixin(models.Model):
    """
    Abstract base class for models that needs optional faculty relationship.
    """
    faculty = models.ForeignKey(
        Faculty,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        abstract = True

class ProgramNullMixin(FacultyMixin):
    """
    Abstract base class for models that needs optional program relationship.
    """
    program = models.ForeignKey(Program, null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        if self.program and self.faculty != self.program.faculty:
            raise ValidationError({'program': 'The selected program does not belong to the assigned faculty.'})

class FacultiesNullMixin(models.Model):
    """
    Abstract base class for models that needs optional multiple faculty relationships.
    """
    faculties = models.ManyToManyField(Faculty, blank = True,)

    class Meta:
        abstract = True

class OrganizationsNullMixin(FacultiesNullMixin):
    """
    Abstract base class for models that needs optional multiple faculty and program relationships.
    """
    programs = models.ManyToManyField(Program, blank = True)

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