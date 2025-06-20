from django.db import models

# Create your models here.
class Faculty(models.Model):
    name = models.CharField(max_length=255, unique=True)

class Program(models.Model):
    name = models.CharField(max_length=255)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE,)