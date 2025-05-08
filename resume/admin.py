from django.contrib import admin

from .models import CareerInfo, Certification, Resume, Submission


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = (
        "resume_id",
        "user",
        "resume_title",
        "job_category",
        "education_level",
        "school_name",
        "education_state",
        "created_at",
    )
    search_fields = ("resume_title", "user__name", "school_name")
    list_filter = ("education_level", "education_state", "job_category")
    readonly_fields = ("resume_id", "created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(CareerInfo)
class CareerInfoAdmin(admin.ModelAdmin):
    list_display = (
        "career_info_id",
        "resume",
        "company_name",
        "position",
        "employment_period_start",
        "employment_period_end",
        "created_at",
    )
    search_fields = ("company_name", "position", "resume__resume_title")
    list_filter = ("company_name", "position")
    readonly_fields = ("career_info_id", "created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(Certification)
class CertificationAdmin(admin.ModelAdmin):
    list_display = (
        "certification_id",
        "resume",
        "certification_name",
        "issuing_organization",
        "date_acquired",
        "created_at",
    )
    search_fields = (
        "certification_name",
        "issuing_organization",
        "resume__resume_title",
    )
    list_filter = ("issuing_organization",)
    readonly_fields = ("certification_id", "created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = (
        "submission_id",
        "job_posting",
        "user",
        "is_read",
        "memo",
        "created_at",
    )
    search_fields = ("job_posting__job_posting_title", "user__name", "memo")
    list_filter = ("is_read",)
    readonly_fields = ("submission_id", "created_at", "updated_at")
    ordering = ("-created_at",)
