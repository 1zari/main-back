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
        """
        필터링 검색 api
        """

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
                job_keyword_sub=request.GET.getlist("job_keyword_sub"),
                job_keyword_main=request.GET.getlist("job_keyword_main"),
            )
        except ValidationError as e:
            return JsonResponse({"errors": e.errors()}, status=400)
        except Exception as e:
            return JsonResponse(
                {"errors": f"Invalid query parameters: {e}"}, status=400
            )


        qs = (
            JobPosting.objects.select_related("company_id")
            .only(
                "job_posting_id",
                "job_posting_title",
                "city",
                "district",
                "town",
                "deadline",
                "location",
                "summary",
                "company_id__company_name",
                "work_day",
                "posting_type",
                "employment_type",
                "education",
                "job_keyword_main",
                "job_keyword_sub",
            )
            .all()
        )

        if query.work_day:
            qs = qs.filter(work_day__overlap=query.work_day)
        if query.posting_type:
            qs = qs.filter(posting_type__in=query.posting_type)
        if query.employment_type:
            qs = qs.filter(employment_type__in=query.employment_type)
        if query.education:
            qs = qs.filter(education=query.education)
        if query.job_keyword_main:
            qs = qs.filter(job_keyword_main__in=query.job_keyword_main)
        if query.job_keyword_sub:
            qs = qs.filter(job_keyword_sub__in=query.job_keyword_sub)
        if query.search:
            qs = qs.filter(
                Q(job_posting_title__icontains=query.search)
                | Q(summary__icontains=query.search)
                | Q(company_id__company_name__icontains=query.search)
            )

        region_qs = District.objects.only(
            "geometry", "city_name", "district_name", "emd_name"
        ).all()
        if query.city:
            region_qs = region_qs.filter(city_name__in=query.city)
        if query.district:
            region_qs = region_qs.filter(district_name__in=query.district)
        if query.town:
            region_qs = region_qs.filter(emd_name__in=query.town)

        job_posting_ids: Set[UUID] = set()

        # 공간 검색 (경계면 기준 3km 포함)
        if region_qs.exists() and query.town:
            distance_q = Q()
            for region in region_qs:
                if region.geometry:
                    # 각 행정구역 경계에서 3km 이내 공고 검색 (공간 인덱스 활용)
                    distance_q |= Q(
                        location__dwithin=(region.geometry, D(km=3))
                    )
            nearby_qs = qs.filter(distance_q).distinct()
            job_posting_ids = set(
                nearby_qs.values_list("job_posting_id", flat=True)
            )
        else:
            job_posting_ids = set(qs.values_list("job_posting_id", flat=True))

        final_qs = (
            JobPosting.objects.select_related("company_id")
            .filter(job_posting_id__in=list(job_posting_ids))
            .only(
                "job_posting_id",
                "job_posting_title",
                "city",
                "district",
                "deadline",
                "summary",
                "company_id__company_logo",
            )
            .all()
        )

        # 북마크 일괄 조회 (N+1 방지)
        bookmarked_ids = set()
        if user_id_for_bookmark:
            bookmarked_ids = set(
                JobPostingBookmark.objects.filter(
                    user_id=user_id_for_bookmark,
                    job_posting_id__in=final_qs.values_list(
                        "job_posting_id", flat=True
                    ),
                ).values_list("job_posting_id", flat=True)
            )

        # 결과 생성
        results: list[JobPostingResultModel] = []
        for jp in final_qs:
            is_bookmarked = jp.job_posting_id in bookmarked_ids
            results.append(
                JobPostingResultModel(
                    job_posting_id=jp.job_posting_id,
                    job_posting_title=jp.job_posting_title,
                    city=jp.city,
                    district=jp.district,
                    is_bookmarked=is_bookmarked,
                    deadline=jp.deadline,
                    summary=jp.summary,
                    company_logo=jp.company_id.company_logo,
                )
            )

        response = JobPostingSearchResponseModel(results=results)
        return JsonResponse(response.model_dump(), status=200)
