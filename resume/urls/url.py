from django.urls.conf import path

from resume.views.resume_views import MyResumeDetailView, MyResumeListView

app_name = "resume"


urlpatterns = [
    path("", MyResumeListView.as_view(), name="resume"),
    path(
        "<uuid:resume_id>/", MyResumeDetailView.as_view(), name="resume_detail"
    ),
]
