from django.db import models
from django.core.exceptions import ValidationError
from .models import Faculty, Program

class OrganizationMixin(models.Model):
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.PROTECT,
        related_name='%(class)s_set_by_faculty', # Dynamic related_name
    )
    program = models.ForeignKey(
        Program,
        on_delete=models.PROTECT,
        related_name='%(class)s_set_by_program', # Dynamic related_name
    )

    def clean(self):
        super().clean()
        if self.program and self.faculty:
            if self.faculty != self.program.faculty:
                raise ValidationError({'program': 'The selected program does not belong to the assigned faculty.'})
    
    class Meta:
        abstract = True

class OrganizationNullMixin(models.Model):
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_set_by_faculty', # Dynamic related_name
    )
    program = models.ForeignKey(
        Program,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_set_by_program', # Dynamic related_name
    )

    def clean(self):
        super().clean()
        if self.program and self.faculty:
            if self.faculty != self.program.faculty:
                raise ValidationError({'program': 'The selected program does not belong to the assigned faculty.'})
    class Meta:
        abstract = True

class FacultyMixin(models.Model):
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.SET_DEFAULT,
        default=None,
        related_name='%(class)s_set_by_faculty', # Dynamic related_name
        help_text="The faculty this record is associated with."
    )

    class Meta:
        abstract = True


class FacultyNullMixin(models.Model):
    faculty = models.ForeignKey(
        Faculty,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Faculty",
        related_name='%(class)s_set_by_faculty', # Dynamic related_name
    )

    class Meta:
        abstract = True

class FacultiesNullMixin(models.Model):
    faculties = models.ManyToManyField(Faculty, blank=True, null=True)

    class Meta:
        abstract = True

class OrganizationsNullMixin(FacultiesNullMixin):
    programs = models.ManyToManyField(Program, blank=True, null=True)

    class Meta:
        abstract = True
