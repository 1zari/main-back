from django.contrib import admin
from django.urls import include, path
from utils.csrf_views import get_csrf_token
urlpatterns = [
    path("api/admin/", admin.site.urls),
    path("api/resume/", include("resume.urls.resume_urls")),
    path("api/submission/", include("resume.urls.submission_urls")),
    path("api/job-postings/", include("job_posting.urls.urls")),
    path("api/user/", include("user.urls.urls")),
    path("api/search/", include("search.urls.search_urls")),
    path("api/csrf/", get_csrf_token),
]
