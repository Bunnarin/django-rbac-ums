# Generated by Django 5.2.3 on 2025-07-22 01:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('academic', '0001_initial'),
        ('organization', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='schedule',
            name='professor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='users.professor'),
        ),
        migrations.AddField(
            model_name='schedule',
            name='program',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='organization.program'),
        ),
        migrations.AlterUniqueTogether(
            name='course',
            unique_together={('faculty', 'program', 'name')},
        ),
        migrations.AlterUniqueTogether(
            name='schedule',
            unique_together={('professor', 'course', '_class', 'faculty', 'program')},
        ),
    ]
