from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from bulk_update_or_create import BulkUpdateOrCreateQuerySet
from django_jsonform.models.fields import JSONField
from apps.organization.mixins import OrganizationMixin
from apps.users.models import User, Student
from apps.core.managers import RLSManager

class Course(OrganizationMixin):
    name = models.CharField(max_length=255)
    year = models.CharField(max_length=1)

    def __str__(self):
        return self.name
    
    class Meta:
        unique_together = ('faculty', 'program', 'name', 'year')
    
    def get_user_rls_filter(self, user):
        return Q(False)

class Class(OrganizationMixin):
    generation = models.IntegerField()
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = "Classes"
        unique_together = ('faculty', 'program', 'generation', 'name')

    def __str__(self):
        return f"{self.generation}: {self.name}"

    def get_user_rls_filter(self, user):
        # the class one is teaching or the class one is a student in
        return Q(students__user=user) | Q(schedule__professor=user)

class Schedule(models.Model):
    """
    Stores the schedule for a professor for a course for a class
    """
    professor = models.ForeignKey(User, on_delete=models.PROTECT)
    course = models.ForeignKey(Course, on_delete=models.PROTECT)
    _class = models.ForeignKey(Class, on_delete=models.PROTECT, related_name="schedules")
    monday = models.CharField(max_length=13, null=True, blank=True)
    tuesday = models.CharField(max_length=13, null=True, blank=True)
    wednesday = models.CharField(max_length=13, null=True, blank=True)
    thursday = models.CharField(max_length=13, null=True, blank=True)
    friday = models.CharField(max_length=13, null=True, blank=True)
    saturday = models.CharField(max_length=13, null=True, blank=True)
    sunday = models.CharField(max_length=13, null=True, blank=True)

    objects = RLSManager(field_with_affiliation="course")

    def get_user_rls_filter(self, user):
        return Q(_class__students__user=user) | Q(professor=user)
    
    def __str__(self):
        return f"{self.professor} - {self.course} - {self._class}"
    
    class Meta:
        unique_together = ('professor', 'course', '_class')
    
class Score(models.Model):
    student = models.ForeignKey(Student, on_delete=models.PROTECT)
    course = models.ForeignKey(Course, on_delete=models.PROTECT)
    score = models.IntegerField()

    objects = BulkUpdateOrCreateQuerySet.as_manager()

    class Meta:
        unique_together = ('student', 'course')

class EvalationTemplate(models.Model):
    """
    This is a singleton model
    """
    TEMPLATE_SCHEMA = {
        "type": "array",
        "items": {
            "type": "object",
            "keys": {
                "title": {"type": "string"},
                "type": {"type": "string",
                        "choices": [
                            "text",
                            "paragraph",
                            "integer",
                            "number",
                            "date",
                            "date-time",
                            "time",
                            "dropdown",
                            "checkbox"
                        ]},
                "required": {"type": "boolean"},
                "choices": {"type": "array", "items": {"type": "string"}}
            }
        }
    }
    question_definition = JSONField(schema=TEMPLATE_SCHEMA)

class Evaluation(models.Model):
    schedule = models.ForeignKey(Schedule, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    response = models.JSONField()

    objects = RLSManager(field_with_affiliation="schedule.course")

    class Meta:
        unique_together = ('schedule', 'student')
    
        