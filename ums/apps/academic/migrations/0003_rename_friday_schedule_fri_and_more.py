# Generated by Django 5.2.3 on 2025-08-01 16:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('academic', '0002_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='schedule',
            old_name='friday',
            new_name='fri',
        ),
        migrations.RenameField(
            model_name='schedule',
            old_name='monday',
            new_name='mon',
        ),
        migrations.RenameField(
            model_name='schedule',
            old_name='saturday',
            new_name='sat',
        ),
        migrations.RenameField(
            model_name='schedule',
            old_name='sunday',
            new_name='sun',
        ),
        migrations.RenameField(
            model_name='schedule',
            old_name='thursday',
            new_name='thu',
        ),
        migrations.RenameField(
            model_name='schedule',
            old_name='tuesday',
            new_name='tue',
        ),
        migrations.RenameField(
            model_name='schedule',
            old_name='wednesday',
            new_name='wed',
        ),
    ]
