# Generated by Django 5.2 on 2025-04-15 04:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        (
            "resume",
            "0007_remove_resume_education_resume_education_level_and_more",
        ),
    ]

    operations = [
        migrations.RenameField(
            model_name="certification",
            old_name="issuing_organizatio",
            new_name="issuing_organization",
        ),
    ]
