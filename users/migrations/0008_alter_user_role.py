# Generated by Django 5.2.1 on 2025-05-19 16:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_alter_user_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(choices=[('student', 'Étudiant'), ('teacher', 'Enseignant'), ('admin', 'admin')], max_length=10),
        ),
    ]
