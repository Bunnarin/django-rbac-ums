# Generated by Django 5.2.3 on 2025-07-22 01:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('organization', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Class',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('faculty', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='organization.faculty')),
                ('program', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='organization.program')),
            ],
            options={
                'verbose_name_plural': 'Classes',
            },
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('faculty', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='organization.faculty')),
                ('program', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='organization.program')),
            ],
        ),
        migrations.CreateModel(
            name='Schedule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('monday', models.CharField(blank=True, max_length=255, null=True)),
                ('tuesday', models.CharField(blank=True, max_length=255, null=True)),
                ('wednesday', models.CharField(blank=True, max_length=255, null=True)),
                ('thursday', models.CharField(blank=True, max_length=255, null=True)),
                ('friday', models.CharField(blank=True, max_length=255, null=True)),
                ('saturday', models.CharField(blank=True, max_length=255, null=True)),
                ('sunday', models.CharField(blank=True, max_length=255, null=True)),
                ('_class', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic.class')),
                ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='academic.course')),
                ('faculty', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='organization.faculty')),
            ],
        ),
    ]
