from typing import Set
from uuid import UUID

from django.contrib.auth.models import AnonymousUser
from django.contrib.gis.measure import D
from django.db.models import Q
from django.http.request import HttpRequest
from django.http.response import JsonResponse
from django.views import View
from pydantic import ValidationError

from job_posting.models import JobPosting, JobPostingBookmark
from search.models import District
from search.schemas import (
    JobPostingResultModel,
    JobPostingSearchQueryModel,
    JobPostingSearchResponseModel,
)
from user.models import CommonUser


class SearchView(View):

    def get(self, request: HttpRequest) -> JsonResponse:
        current_user: CommonUser | AnonymousUser = request.user
        user_id_for_bookmark = None
        if current_user.is_authenticated:
            user_id_for_bookmark = current_user.common_user_id

        try:
            query = JobPostingSearchQueryModel(
                city=request.GET.getlist("city"),
                district=request.GET.getlist("district"),
                town=request.GET.getlist("town"),
                work_day=request.GET.getlist("work_day"),
                posting_type=request.GET.getlist("posting_type"),
                employment_type=request.GET.getlist("employment_type"),
                education=request.GET.get("education", ""),
                search=request.GET.get("search", ""),
            )
        except ValidationError as e:
            return JsonResponse({"errors": e.errors()}, status=400)
        except Exception as e:
            return JsonResponse(
                {"errors": f"Invalid query parameters: {e}"}, status=400
            )

        qs = JobPosting.objects.all()
        if query.city:
            qs = qs.filter(city__in=query.city)
        if query.district:
            qs = qs.filter(district__in=query.district)
        if query.town:
            qs = qs.filter(town__in=query.town)
        if query.work_day:
            qs = qs.filter(work_day__overlap=query.work_day)
        if query.posting_type:
            qs = qs.filter(posting_type__in=query.posting_type)
        if query.employment_type:
            qs = qs.filter(employment_type__in=query.employment_type)
        if query.education:
            qs = qs.filter(education=query.education)

        if query.search:
            qs = qs.filter(
                Q(job_posting_title__icontains=query.search)
                | Q(summary__icontains=query.search)
                | Q(company_id__company_name__icontains=query.search)
            )

        region_qs = District.objects.all()
        if query.city:
            region_qs = region_qs.filter(city_name__in=query.city)
        if query.district:
            region_qs = region_qs.filter(district_name__in=query.district)
        if query.town:
            region_qs = region_qs.filter(emd_name__in=query.town)

        job_posting_ids: Set[UUID] = set()

        if region_qs.exists() or (
            not query.city and not query.district and not query.town
        ):
            target_regions = (
                region_qs if region_qs.exists() else District.objects.all()
            )
            for region in target_regions:
                if region.geometry:
                    center_point = region.geometry.centroid
                    nearby_qs = qs.filter(
                        location__distance_lte=(center_point, D(km=3))
                    )
                    job_posting_ids.update(
                        nearby_qs.values_list("job_posting_id", flat=True)
                    )

        final_qs = JobPosting.objects.filter(
            job_posting_id__in=list(job_posting_ids)
        )

        results: list[JobPostingResultModel] = []
        for jp in final_qs:

            is_bookmarked = False
            if user_id_for_bookmark is not None:

                is_bookmarked = JobPostingBookmark.objects.filter(
                    job_posting=jp, user_id=user_id_for_bookmark
                ).exists()

            results.append(
                JobPostingResultModel(
                    job_posting_id=jp.job_posting_id,
                    job_posting_title=jp.job_posting_title,
                    city=jp.city,
                    district=jp.district,
                    is_bookmarked=is_bookmarked,
                    deadline=jp.deadline,
                )
            )

        response = JobPostingSearchResponseModel(results=results)
        return JsonResponse(response.model_dump(), status=200)
