from django.db import models
from django.db.models import Q
from apps.organization.mixins import OrganizationMixin
from apps.users.models import Professor
from apps.core.managers import RLSManager

class Course(OrganizationMixin):
    name = models.CharField(max_length=255)

    objects = RLSManager()

    def __str__(self):
        return self.name
    
    class Meta:
        unique_together = ('faculty', 'program', 'name')

class Class(OrganizationMixin):
    name = models.CharField(max_length=255)

    objects = RLSManager()

    class Meta:
        verbose_name_plural = "Classes"

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """
        Generate a unique name for the class
        """
        creation = not self.pk
        if creation:
            name_num = self.__class__.objects.filter(faculty=self.faculty, program=self.program, name__startswith=self.name).count()
            if name_num > 0:
                self.name = self.name + " " + str(name_num)
        super().save(*args, **kwargs)

class Schedule(models.Model):
    """
    Stores the schedule for a professor for a course for a class
    """
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    _class = models.ForeignKey(Class, on_delete=models.CASCADE)
    monday = models.CharField(max_length=255, null=True, blank=True)
    tuesday = models.CharField(max_length=255, null=True, blank=True)
    wednesday = models.CharField(max_length=255, null=True, blank=True)
    thursday = models.CharField(max_length=255, null=True, blank=True)
    friday = models.CharField(max_length=255, null=True, blank=True)
    saturday = models.CharField(max_length=255, null=True, blank=True)
    sunday = models.CharField(max_length=255, null=True, blank=True)

    objects = RLSManager()

    def get_user_rls_filter(self, user):
        return Q(_class__students__user=user) | Q(professor__user=user)
    
    def __str__(self):
        return f"{self.professor} - {self.course} - {self._class}"
    
    class Meta:
        unique_together = ('professor', 'course', '_class')
        