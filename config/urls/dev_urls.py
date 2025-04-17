from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("api/admin/", admin.site.urls),
    path("api/resume/", include("resume.urls.url")),
    path("api/user/", include("user.urls.url")),
    path("api/job-postings/", include("job_posting.urls.urls"))

