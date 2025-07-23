from django.db import models
from django.core.exceptions import ValidationError, ImproperlyConfigured
from apps.core.managers import RLSManager
from .models import Faculty, Program

class OrganizationMixin(models.Model):
    """
    Abstract base class for models with both faculty and program affiliations.
    """
    faculty = models.ForeignKey(Faculty, on_delete=models.PROTECT)
    program = models.ForeignKey(Program, on_delete=models.PROTECT)
    objects = RLSManager()

    def get_user_rls_filter(self, user):
        """
        Raise error to enforce any subclasses to define this method
        """
        raise ImproperlyConfigured("Subclasses must implement get_user_rls_filter method")

    def clean(self):
        super().clean()
        """
        this is to ensure that get_user_rls_filter is implemented
        """
        self.get_user_rls_filter(None)
        if self.program and self.faculty and self.faculty != self.program.faculty:
            raise ValidationError({
                'program': 'The selected program does not belong to the assigned faculty.'
                })

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
    
    def get_user_rls_filter(self, user):
        """
        Raise error to enforce any subclasses to define this method
        """
        raise ImproperlyConfigured("Subclasses must implement get_user_rls_filter method")
    
    def clean(self):
        super().clean()
        """
        this is to ensure that get_user_rls_filter is implemented
        """
        self.get_user_rls_filter(None)

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
        self.get_user_rls_filter(None)
        if self.program and self.faculty and self.faculty != self.program.faculty:
            raise ValidationError({'program': 'The selected program does not belong to the assigned faculty.'})

    def save(self, *args, **kwargs):
        """
        Validate that the selected program belongs to the selected faculty.
        we do it in save and not clean because the form needs to inject affiliation after the clean
        """
        if self.program and self.faculty != self.program.faculty:
            raise ValidationError({'program': 'The selected program does not belong to the assigned faculty.'})
        super().save(*args, **kwargs)
    
    def get_user_rls_filter(self, user):
        """
        Raise error to enforce any subclasses to define this method
        """
        raise ImproperlyConfigured("Subclasses must implement get_user_rls_filter method")
        