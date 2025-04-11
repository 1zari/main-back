# Generated by Django 5.2 on 2025-04-11 02:46

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="CommonUser",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="작성일자"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, verbose_name="작성일자"
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("email", models.EmailField(max_length=50, unique=True)),
                ("password", models.CharField(max_length=255)),
                ("join_type", models.CharField(max_length=10)),
                ("last_login", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="CompanyInfo",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="작성일자"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, verbose_name="작성일자"
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("company_name", models.CharField(max_length=50)),
                ("establishment", models.DateField()),
                ("company_address", models.CharField(max_length=100)),
                (
                    "business_registration_number",
                    models.CharField(max_length=20),
                ),
                ("company_introduction", models.TextField()),
                ("certificate_image", models.URLField()),
                ("manager_name", models.CharField(max_length=30)),
                ("manager_phone_number", models.CharField(max_length=30)),
                ("manager_email", models.EmailField(max_length=50)),
                ("is_active", models.BooleanField(default=False)),
                ("is_staff", models.BooleanField(default=False)),
                (
                    "common_user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="user.commonuser",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="UserInfo",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="작성일자"
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True, verbose_name="작성일자"
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=30)),
                ("phone_number", models.CharField(max_length=20, unique=True)),
                ("gender", models.CharField(max_length=10)),
                ("birthday", models.DateField(blank=True, null=True)),
                ("interest", models.JSONField(default=list)),
                ("purpose_subscription", models.JSONField(default=list)),
                ("route", models.JSONField(default=list)),
                ("is_active", models.BooleanField(default=False)),
                (
                    "common_user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="user.commonuser",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
