from django.db import models

# Create your models here.
class Faculty(models.Model):
    name = models.CharField(max_length=255, unique=True)
    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Faculties"

class Program(models.Model):
    name = models.CharField(max_length=255)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE,)
    def __str__(self):
        return self.name
