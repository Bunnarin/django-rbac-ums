# Generated by Django 5.2.3 on 2025-07-22 03:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academic', '0002_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='schedule',
            unique_together={('professor', 'course', '_class')},
        ),
        migrations.RemoveField(
            model_name='schedule',
            name='faculty',
        ),
        migrations.RemoveField(
            model_name='schedule',
            name='program',
        ),
    ]
