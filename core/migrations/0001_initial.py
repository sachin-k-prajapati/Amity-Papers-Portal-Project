# Generated by Django 5.2.4 on 2025-07-13 10:17

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Institute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('abbreviation', models.CharField(blank=True, help_text='Short form (e.g., ASET, ALS, etc.)', max_length=20, null=True)),
                ('icon', models.ImageField(blank=True, null=True, upload_to='institutes/')),
            ],
        ),
        migrations.CreateModel(
            name='Subject',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('code', models.CharField(max_length=20)),
            ],
        ),
        migrations.CreateModel(
            name='Program',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('institute', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='programs', to='core.institute')),
            ],
        ),
        migrations.CreateModel(
            name='Semester',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveSmallIntegerField()),
                ('program', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='semesters', to='core.program')),
            ],
            options={
                'ordering': ['number'],
                'unique_together': {('program', 'number')},
            },
        ),
        migrations.CreateModel(
            name='SubjectOffering',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('semester', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subject_offerings', to='core.semester')),
                ('subject', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='offerings', to='core.subject')),
            ],
        ),
        migrations.AddField(
            model_name='subject',
            name='semesters',
            field=models.ManyToManyField(through='core.SubjectOffering', to='core.semester'),
        ),
        migrations.CreateModel(
            name='ExamPaper',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('paper_type', models.CharField(choices=[('E', 'End Sem'), ('B', 'Back Paper')], max_length=1)),
                ('year', models.PositiveIntegerField()),
                ('file', models.FileField(upload_to='papers/')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('subject_offering', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exam_papers', to='core.subjectoffering')),
            ],
        ),
    ]
