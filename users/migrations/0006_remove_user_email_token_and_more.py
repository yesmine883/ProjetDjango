# Generated by Django 5.2.1 on 2025-05-17 12:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_user_email_token_user_email_token_created_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='user',
            name='email_token',
        ),
        migrations.RemoveField(
            model_name='user',
            name='email_token_created',
        ),
        migrations.RemoveField(
            model_name='user',
            name='email_verified',
        ),
        migrations.RemoveField(
            model_name='user',
            name='password_reset_token',
        ),
        migrations.RemoveField(
            model_name='user',
            name='password_reset_token_created',
        ),
    ]
