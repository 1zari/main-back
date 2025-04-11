# Generated by Django 5.2 on 2025-04-11 04:43

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("user", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="commonuser",
            old_name="id",
            new_name="common_user_id",
        ),
        migrations.RenameField(
            model_name="companyinfo",
            old_name="id",
            new_name="company_id",
        ),
        migrations.RenameField(
            model_name="userinfo",
            old_name="id",
            new_name="user_id",
        ),
        migrations.AddField(
            model_name="companyinfo",
            name="ceo_name",
            field=models.CharField(default="대표", max_length=20),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="userinfo",
            name="wish_work_place",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name="userinfo",
            name="interest",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=50),
                blank=True,
                default=list,
                size=None,
            ),
        ),
        migrations.AlterField(
            model_name="userinfo",
            name="purpose_subscription",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=50),
                blank=True,
                default=list,
                size=None,
            ),
        ),
        migrations.AlterField(
            model_name="userinfo",
            name="route",
            field=django.contrib.postgres.fields.ArrayField(
                base_field=models.CharField(max_length=50),
                blank=True,
                default=list,
                size=None,
            ),
        ),
    ]
