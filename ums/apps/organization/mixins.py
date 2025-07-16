from django.db import models
from django.core.exceptions import ValidationError
from .models import Faculty, Program

class OrganizationMixin(models.Model):
    """
    Abstract base class for models that require both faculty and program relationships.
    
    Provides required relationships to Faculty and Program models with validation
    to ensure program belongs to the selected faculty.
    
    Attributes:
        faculty: Required ForeignKey to Faculty model
        program: Required ForeignKey to Program model
    
    Methods:
        clean(): Validates that the selected program belongs to the selected faculty
    """
    faculty = models.ForeignKey(Faculty, on_delete=models.PROTECT,)
    program = models.ForeignKey(Program, on_delete=models.PROTECT,)

    def clean(self):
        """
        Validate that the selected program belongs to the selected faculty.
        
        Raises:
            ValidationError: If the program does not belong to the selected faculty
        """
        super().clean()
        if self.program and self.faculty:
            if self.faculty != self.program.faculty:
                raise ValidationError({'program': 'The selected program does not belong to the assigned faculty.'})
    
    class Meta:
        abstract = True

class OrganizationNullMixin(models.Model):
    """
    Abstract base class for models that require optional faculty and program relationships.
    
    Similar to OrganizationMixin but allows null values for faculty and program.
    
    Attributes:
        faculty: Optional ForeignKey to Faculty model
        program: Optional ForeignKey to Program model
    
    Methods:
        clean(): Validates that the selected program belongs to the selected faculty
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
    
    Provides a required relationship to the Faculty model. Uses PROTECT
    on delete to maintain referential integrity.
    
    Attributes:
        faculty: Required ForeignKey to Faculty model
    """
    faculty = models.ForeignKey(Faculty, on_delete=models.PROTECT)

    class Meta:
        abstract = True

class FacultyNullMixin(models.Model):
    """
    Abstract base class for models that require an optional faculty relationship.
    
    Provides an optional relationship to the Faculty model that can be null.
    
    Attributes:
        faculty: Optional ForeignKey to Faculty model
    """
    faculty = models.ForeignKey(
        Faculty,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        abstract = True

class FacultiesNullMixin(models.Model):
    """
    Abstract base class for models that require multiple faculty relationships.
    
    Provides a ManyToMany relationship to the Faculty model that can be empty.
    
    Attributes:
        faculties: ManyToManyField to Faculty model
    """
    faculties = models.ManyToManyField(Faculty, blank = True,)

    class Meta:
        abstract = True

class OrganizationsNullMixin(FacultiesNullMixin):
    """
    Abstract base class for models that require multiple faculty and program relationships.
    
    Attributes:
        faculties: ManyToManyField to Faculty model (inherited)
        programs: ManyToManyField to Program model
    """
    programs = models.ManyToManyField(Program, blank = True)

    class Meta:
        abstract = True
