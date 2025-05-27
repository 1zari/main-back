from django.urls.conf import path

from search.views.search_views import SearchView
from search.views.tree_views import JobTreeView, RegionTreeView

app_name = "search"


urlpatterns = [
    path("region/", RegionTreeView.as_view(), name="region_tree"),
    path("", SearchView.as_view(), name="search"),
    path("job/", JobTreeView.as_view(), name="job_tree"),
]
