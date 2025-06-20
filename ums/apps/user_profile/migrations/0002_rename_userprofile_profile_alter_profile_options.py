# Generated by Django 5.2.3 on 2025-06-20 06:02

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('organization', '0001_initial'),
        ('user_profile', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameModel(
            old_name='UserProfile',
            new_name='Profile',
        ),
        migrations.AlterModelOptions(
            name='profile',
            options={'permissions': [('access_faculty_wide', 'Can access all data within their assigned faculty'), ('access_global', 'Can access all data across all faculties and programs')]},
        ),
    ]
