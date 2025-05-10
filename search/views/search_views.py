from django.contrib.gis.db.models.aggregates import Union
from django.contrib.gis.measure import D
from django.db.models import Q
from django.db.models.expressions import Exists, OuterRef
from django.http import HttpRequest, JsonResponse
from django.views import View
from pydantic import ValidationError
from django.db.models import Func, CharField
from django.contrib.postgres.fields import ArrayField

from job_posting.models import JobPosting, JobPostingBookmark
from search.models import District
from search.schemas import (
    JobPostingResultModel,
    JobPostingSearchQueryModel,
    JobPostingSearchResponseModel,
)
from user.models import CommonUser
from utils.common import get_user_from_token, get_valid_normal_user


class SearchView(View):
    def get(self, request: HttpRequest) -> JsonResponse:
        valid_user: CommonUser = get_user_from_token(request)
        current_user = get_valid_normal_user(valid_user) if valid_user else None

        try:
            query = JobPostingSearchQueryModel(
                city_no=request.GET.getlist("city_no"),  # 시도 id
                district_no=request.GET.getlist("district_no"),  # 시군구 id
                town_no=request.GET.getlist("town_no"),  # 읍면동 id
                work_day=request.GET.getlist("work_day"),  # 근무 요일
                day_discussion=request.GET.get("day_discussion") == "true",
                posting_type=request.GET.get("posting_type", ""),  # 공고 형태 공공, 기업
                employment_type=request.GET.getlist("employment_type"),  # 고용형태 정규직, 계약직
                education=request.GET.getlist("education"),  # 학력사항
                search=request.GET.get("search", ""),  # 공고 제목, 기업, 근무요약 키워드
                job_keyword_sub=request.GET.getlist("job_keyword_sub"),  # 직종 소분류
                job_keyword_main=request.GET.getlist("job_keyword_main"),  # 직종 대분류
                work_experience=request.GET.getlist("work_experience"),  # 경력사항
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

        qs = (
            JobPosting.objects.select_related("company_id")
            .defer("location", "work_day", "posting_type", "employment_type")
            .filter(
                Q(work_day__overlap=query.work_day) if query.work_day else Q(),
                Q(posting_type__in=query.posting_type) if query.posting_type else Q(),
                Q(employment_type__in=query.employment_type) if query.employment_type else Q(),
                Q(education__in=query.education) if query.education else Q(),
                Q(work_experience__in=query.work_experience) if query.work_experience else Q(),
                Q(day_discussion__in=query.day_discussion) if query.day_discussion else Q(),
                Q(job_keyword_main__overlap=Func(
                    query.job_keyword_main,
                    function='ARRAY',
                    template="%(function)s[%(expressions)s]::varchar[]",
                    output_field=ArrayField(CharField())
                )) if query.job_keyword_main else Q(),
                Q(job_keyword_sub__overlap=Func(
                    query.job_keyword_sub,
                    function='ARRAY',
                    template="%(function)s[%(expressions)s]::varchar[]",
                    output_field=ArrayField(CharField())
                )) if query.job_keyword_sub else Q(),
                Q(work_experience__in=query.work_experience) if query.work_experience else Q(),
            )
        )

        # 2. 검색 조건 최적화
        if query.search:
            qs = qs.filter(
                Q(job_posting_title__icontains=query.search)
                | Q(summary__icontains=query.search)
                | Q(company_id__company_name__icontains=query.search)
            )

        # 3. 지역 필터링 (데이터베이스 레벨에서 처리)
        district_filter = Q()
        if query.city_no:
            district_filter &= Q(city_no__in=query.city_no)
        if query.district_no:
            district_filter &= Q(district_no__in=query.district_no)
        if query.town_no:
            district_filter &= Q(emd_no__in=query.town_no)

        # 4. 공간 쿼리 최적화 (ST_Union + ST_DWithin)
        if query.town_no and (
            regions := District.objects.filter(district_filter).aggregate(Union("geometry"))["geometry__union"]
        ):
            regions_3km = regions.buffer(3000)  # 3km 버퍼
            qs = qs.filter(location__dwithin=(regions_3km, D(km=0)))

        # 5. 북마크 정보 서브쿼리
        if current_user:
            bookmarked = JobPostingBookmark.objects.filter(
                user_id=current_user.common_user_id, job_posting_id=OuterRef("pk")
            )
            qs = qs.annotate(is_bookmarked=Exists(bookmarked))

        # 6. 최종 결과 쿼리
        final_qs = qs.only(
            "job_posting_id", "job_posting_title", "city", "district", "deadline", "summary", "company_id__company_logo"
        )

        # 7. 결과 직렬화
        results = [
            JobPostingResultModel(
                job_posting_id=jp.job_posting_id,
                job_posting_title=jp.job_posting_title,
                city=jp.city,
                district=jp.district,
                is_bookmarked=jp.is_bookmarked if hasattr(jp, "is_bookmarked") else False,
                deadline=jp.deadline,
                summary=jp.summary,
                company_logo=jp.company_id.company_logo,
            )
            for jp in final_qs
        ]

        return JsonResponse(JobPostingSearchResponseModel(results=results).model_dump(), safe=False)
