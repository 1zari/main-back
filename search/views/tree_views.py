import json
from typing import Dict, List, cast

import redis
from django.http import JsonResponse
from django.views import View

from config.settings.base import REDIS_DB, REDIS_HOST, REDIS_PORT
from search.schemas import JobTreeResponse, RegionTreeResponse

r = redis.Redis(
    host=cast(str, REDIS_HOST),
    port=cast(int, REDIS_PORT),
    db=cast(int, REDIS_DB),
    decode_responses=True,
)


class RegionTreeView(View):
    def get(self, request) -> JsonResponse:
        region_tree_json = r.get("region_tree")

        region_tree = json.loads(region_tree_json) if region_tree_json else {}

        response_model = RegionTreeResponse.model_validate(region_tree)
        return JsonResponse(
            response_model.model_dump(),
            status=200,
            safe=False,
            json_dumps_params={"ensure_ascii": False},
        )


class JobTreeView(View):
    def get(self, request) -> JsonResponse:
        job_tree_json = r.get("job_categories")
        job_tree = json.loads(job_tree_json) if job_tree_json else {}

        response_model = JobTreeResponse.model_validate(job_tree)
        return JsonResponse(
            response_model.model_dump(),
            safe=False,
            json_dumps_params={"ensure_ascii": False},
            status=200,
        )
