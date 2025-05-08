from django.urls import path

from ..views.views import (
    JobPostingBookmarkView,
    JobPostingDetailView,
    JobPostingListView,
)

urlpatterns = [
    # 공고 리스트 조회
    path("", JobPostingListView.as_view(), name="job_posting_list"),
    # 공고 상세 조회, 수정, 삭제
    path(
        "<uuid:job_posting_id>/",
        JobPostingDetailView.as_view(),
        name="job_posting_detail",
    ),
    # 공고 생성
    path("create/", JobPostingDetailView.as_view(), name="job_posting_create"),
    # 북마크 목록 조회
    path("bookmark/", JobPostingBookmarkView.as_view(), name="bookmark_list"),
    # 북마크 등록/삭제
    path(
        "bookmark/<uuid:job_posting_id>/",
        JobPostingBookmarkView.as_view(),
        name="bookmark_toggle",
    ),
]
