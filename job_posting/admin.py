from django.contrib import admin

from job_posting.models import JobPosting


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = (
        "job_posting_title",
        "company_id",
        "posting_type",
        "employment_type",
        "number_of_positions",
        "education",
        "deadline",
        "time_discussion",
        "day_discussion",
        "salary_type",
        "salary",
    )
    search_fields = ("job_posting_title", "company_id__company_name")
    list_filter = (
        "posting_type",
        "employment_type",
        "education",
        "salary_type",
    )
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "job_posting_title",
                    "company_id",
                    "location",
                    ("work_time_start", "work_time_end"),
                    ("posting_type", "employment_type"),
                    "job_keyword_main",
                    "job_keyword_sub",
                    "number_of_positions",
                    "education",
                    "deadline",
                    ("time_discussion", "day_discussion", "work_day"),
                    ("salary_type", "salary"),
                    "summary",
                    "content",
                    ("created_at", "updated_at"),
                )
            },
        ),
    )
