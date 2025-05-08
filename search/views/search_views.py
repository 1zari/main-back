from typing import List, Set
from uuid import UUID

from django.contrib.auth.models import AnonymousUser
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D
from django.db.models import Q
from django.http import HttpRequest, JsonResponse
from django.views import View
from pydantic import ValidationError

from job_posting.models import JobPosting, JobPostingBookmark
from search.models import District
from search.schemas import (
    DistrictModelDTO,
    JobPostingResultModel,
    JobPostingSearchQueryModel,
    JobPostingSearchResponseModel,
)
from user.models import CommonUser


class SearchView(View):
    def get(self, request: HttpRequest) -> JsonResponse:
        current_user: CommonUser | AnonymousUser = request.user
        user_id_for_bookmark = current_user.common_user_id if current_user.is_authenticated else None

        try:
            query = JobPostingSearchQueryModel(
                city_no=request.GET.getlist("city_no"),
                district_no=request.GET.getlist("district_no"),
                town_no=request.GET.getlist("town_no"),
                work_day=request.GET.getlist("work_day"),
                posting_type=request.GET.getlist("posting_type"),
                employment_type=request.GET.getlist("employment_type"),  # 고용형태
                education=request.GET.get("education", ""),  # 학력사항
                search=request.GET.get("search", ""),
                job_keyword_sub=request.GET.getlist("job_keyword_sub"),
                job_keyword_main=request.GET.getlist("job_keyword_main"),
                work_experience=request.GET.get("work_experience", ""),
            )
        except ValidationError as e:
            return JsonResponse({"errors": e.errors()}, status=400)
        except Exception as e:
            return JsonResponse({"errors": f"Invalid query parameters: {e}"}, status=400)

        # 1. 공고 기본 쿼리셋
        qs = JobPosting.objects.select_related("company_id").only(
            "job_posting_id",
            "job_posting_title",
            "city",
            "district",
            "town",
            "deadline",
            "location",
            "summary",
            "company_id__company_logo",
            "work_day",
            "posting_type",
            "employment_type",
            "education",
            "job_keyword_main",
            "job_keyword_sub",
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

        # 2. District를 DTO로 변환 (only로 필드 제한)
        region_model = District.objects.only("geometry", "city_no", "district_no", "emd_no").all()
        region_dtos: List[DistrictModelDTO] = [DistrictModelDTO.from_orm(obj) for obj in region_model]

        # 3. 지역 필터링 (메모리 내에서 안전하게)
        if query.city_no:
            region_dtos = [dto for dto in region_dtos if dto.city_no in query.city_no]
        if query.district_no:
            region_dtos = [dto for dto in region_dtos if dto.district_no in query.district_no]
        if query.town_no:
            region_dtos = [dto for dto in region_dtos if dto.emd_no in query.town_no]

        job_posting_ids: Set[UUID] = set()

        # 4. 공간검색 (town_no 있을 때만)
        if region_dtos and query.town_no:
            distance_q = Q()
            for region in region_dtos:
                geom = GEOSGeometry(region.geometry, srid=5179)
                distance_q |= Q(location__dwithin=(geom, D(km=3)))
            job_posting_ids = set(qs.filter(distance_q).values_list("job_posting_id", flat=True))
        else:
            job_posting_ids = set(qs.values_list("job_posting_id", flat=True))

        # 5. 최종 공고 쿼리
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
        )

        bookmarked_ids = set()
        if user_id_for_bookmark:
            bookmarked_ids = set(
                JobPostingBookmark.objects.filter(
                    user_id=user_id_for_bookmark,
                    job_posting_id__in=final_qs.values_list("job_posting_id", flat=True),
                ).values_list("job_posting_id", flat=True)
            )

        results = [
            JobPostingResultModel(
                job_posting_id=jp.job_posting_id,
                job_posting_title=jp.job_posting_title,
                city=jp.city,
                district=jp.district,
                is_bookmarked=jp.job_posting_id in bookmarked_ids,
                deadline=jp.deadline,
                summary=jp.summary,
                company_logo=jp.company_id.company_logo,
            )
            for jp in final_qs
        ]

        response = JobPostingSearchResponseModel(results=results)
        return JsonResponse(response.model_dump(), safe=False)
