from django.urls.conf import path

from resume.views.resume_views import MyResumeDetailView, MyResumeListView
from resume.views.submission_views import (
    SubmissionCompanyDetialView,
    SubmissionCompanyListView,
    SubmissionDetailView,
    SubmissionListView,
    SubmissionMemoView,
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
        name="company_submissions",
    ),
    path(
        "company/<uuid:submission_id>/",
        SubmissionCompanyDetialView.as_view(),
        name="company_submission",
    ),
    path(
        "memo/<uuid:submission_id>/",
        SubmissionMemoView.as_view(),
        name="submission_memo",
    ),
]
