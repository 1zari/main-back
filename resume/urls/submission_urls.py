from django.urls.conf import path

from resume.views.resume_views import MyResumeDetailView, MyResumeListView
from resume.views.submission_views import (
    SubmissionCompanyListView,
    SubmissionDetailView,
    SubmissionListView,
)

app_name = "submission"


urlpatterns = [
    path("", SubmissionListView.as_view(), name="submission"),
    path(
        "<uuid:submission_id>/",
        SubmissionDetailView.as_view(),
        name="submission_detail",
    ),
    path(
        "company/",
        SubmissionCompanyListView.as_view(),
        name="company_submission",
    ),
]
