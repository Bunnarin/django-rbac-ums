from django.db import models
from django.core.exceptions import ValidationError
from .models import Faculty, Program

class OrganizationMixin(models.Model):
    """
    Abstract base class that provides faculty and program foreign keys
    for models requiring organizational affiliation.
    """
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Faculty Affiliation",
        related_name='%(class)s_set_by_faculty', # Dynamic related_name
    )
    program = models.ForeignKey(
        Program,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Program Affiliation",
        related_name='%(class)s_set_by_program', # Dynamic related_name
    )

    class Meta:
        abstract = True

class FacultyMixin(models.Model):
    """
    Abstract base class that provides a faculty foreign key
    for models requiring faculty affiliation.
    """
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE,
        verbose_name="Faculty",
        related_name='%(class)s_set_by_faculty', # Dynamic related_name
        help_text="The faculty this record is associated with."
    )

    class Meta:
        abstract = True

class ProgramMixin(models.Model):
    """
    Abstract base class that provides a program foreign key.
    Automatically sets the faculty based on the selected program.
    This mixin should typically be used *instead* of FacultyMixin
    if the entity's primary affiliation is a program.
    """
    program = models.ForeignKey(
        Program,
        on_delete=models.SET_NULL,
        null=True,
        blank=True, # Programs can sometimes be optional on an entity
        verbose_name="Program",
        related_name='%(class)s_set_by_program', # Dynamic related_name
        help_text="The program this record is associated with."
    )

    class Meta:
        abstract = True

    # This method is key for auto-setting the faculty based on program
    def save(self, *args, **kwargs):
        if self.program and not hasattr(self, '_program_faculty_set'):
            if hasattr(self, 'faculty'): # Ensure the model instance actually has a 'faculty' field
                self.faculty = self.program.faculty
                self._program_faculty_set = True # Flag to prevent re-setting if save is called multiple times
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.program:
            if hasattr(self, 'faculty') and self.faculty and self.faculty != self.program.faculty:
                raise ValidationError(
                    {'program': 'The selected program does not belong to the assigned faculty.'}
                )