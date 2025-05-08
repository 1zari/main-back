from django.urls import path

from ..views.views import (
    JobPostingBookmarkView,
    JobPostingDetailView,
    JobPostingListView,
)

urlpatterns = [
    # 공고 리스트 조회 API
    path("job-postings/", JobPostingListView.as_view(), name="job_posting_list"),
    # 공고 상세 조회, 생성, 수정, 삭제 API
    path(
        "job-postings/<uuid:job_posting_id>/",
        JobPostingDetailView.as_view(),
        name="job_posting_detail",
    ),
    # 공고 북마크 등록, 삭제, 조회 API
    path(
        "job-postings/bookmark/",
        JobPostingBookmarkView.as_view(),
        name="job_posting_bookmark_list",
    ),
    path(
        "job-postings/bookmark/<uuid:job_posting_id>/",
        JobPostingBookmarkView.as_view(),
        name="job_posting_bookmark",
    ),
]
