from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from bulk_update_or_create import BulkUpdateOrCreateQuerySet
from django_jsonform.models.fields import JSONField
from apps.organization.mixins import OrganizationMixin
from apps.users.models import CustomUser, Student
from apps.core.mixins import DetailMixin
from apps.core.managers import RLSManager

class Course(DetailMixin, OrganizationMixin):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
    class Meta:
        unique_together = ('faculty', 'program', 'name')
    
    def get_user_rls_filter(self, user):
        """
        return nothing
        """
        return Q()

class Class(DetailMixin, OrganizationMixin):
    generation = models.IntegerField()
    name = models.CharField(max_length=255)

    class Meta:
        verbose_name_plural = "Classes"
        unique_together = ('faculty', 'program', 'generation', 'name')

    def __str__(self):
        return f"{self.generation}: {self.name}"

    def get_user_rls_filter(self, user):
        # the class one is teaching or the class one is a student in
        return Q(student__user=user) | Q(schedule__professor=user)

class Schedule(DetailMixin, models.Model):
    """
    Stores the schedule for a professor for a course for a class
    """
    professor = models.ForeignKey(CustomUser, on_delete=models.PROTECT)
    course = models.ForeignKey(Course, on_delete=models.PROTECT)
    _class = models.ForeignKey(Class, on_delete=models.PROTECT)
    monday = models.CharField(max_length=13, null=True, blank=True)
    tuesday = models.CharField(max_length=13, null=True, blank=True)
    wednesday = models.CharField(max_length=13, null=True, blank=True)
    thursday = models.CharField(max_length=13, null=True, blank=True)
    friday = models.CharField(max_length=13, null=True, blank=True)
    saturday = models.CharField(max_length=13, null=True, blank=True)
    sunday = models.CharField(max_length=13, null=True, blank=True)

    objects = RLSManager(field_with_affiliation="course")

    def get_user_rls_filter(self, user):
        return Q(_class__student__user=user) | Q(professor=user)
    
    def __str__(self):
        return f"{self.professor} - {self.course} - {self._class}"
    
    class Meta:
        unique_together = ('professor', 'course', '_class')
    
    def save(self, *args, **kwargs):
        """
        ensures that the the user added gets added to the ALL PROFESSOR GROUP
        also ensures that the course and the class affiliation match
        """
        # check if the course and the class affiliation match
        if self.course.faculty != self._class.faculty or self.course.program != self._class.program:
            raise ValidationError("Course and class affiliation do not match")
            
        creation = not self.pk
        if not creation:
            # check if the user changed
            old_prof = Schedule.objects.get(pk=self.pk).professor
            if old_prof != self.professor:
                # check if the user has any other schedule, if no, remove their prof status
                if not Schedule.objects.filter(professor=old_prof).exclude(pk=self.pk).exists():
                    old_prof.is_professor = False
                    old_prof.save()
        self.professor.is_professor = True
        self.professor.save()
        super().save(*args, **kwargs)

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
    
        