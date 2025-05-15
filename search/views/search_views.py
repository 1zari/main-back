from django.contrib.gis.db.models.aggregates import Union
from django.contrib.gis.measure import D
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.db.models.expressions import Exists, OuterRef
from django.http import HttpRequest, JsonResponse
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
from utils.common import check_and_return_normal_user, get_user_from_token


class SearchView(View):
    def get(self, request: HttpRequest) -> JsonResponse:
        # 0. 인증된 사용자 가져오기
        valid_user: CommonUser = get_user_from_token(request)
        current_user = check_and_return_normal_user(valid_user) if valid_user else None

        # 1. 쿼리 파라미터 검증 및 파싱
        try:
            query = JobPostingSearchQueryModel(
                city_no=request.GET.getlist("city_no"),  # 시도 id
                district_no=request.GET.getlist("district_no"),  # 시군구 id
                town_no=request.GET.getlist("town_no"),  # 읍면동 id
                work_day=request.GET.getlist("work_day"),  # 근무 요일
                day_discussion=request.GET.get("day_discussion") == "true",
                posting_type=request.GET.getlist("posting_type"),  # 공고 형태 공공, 기업
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

        qs = JobPosting.objects.select_related("company_id").defer("location", "work_day")

        #  필터링 조건 적용
        qs = qs.filter(
            Q(work_day__overlap=query.work_day) if query.work_day else Q(),
            Q(posting_type__in=query.posting_type) if query.posting_type else Q(),
            Q(employment_type__in=query.employment_type) if query.employment_type else Q(),
            Q(education__in=query.education) if query.education else Q(),
            Q(work_experience__in=query.work_experience) if query.work_experience else Q(),
            Q(day_discussion=True) if query.day_discussion else Q(),
            Q(job_keyword_main__in=query.job_keyword_main) if query.job_keyword_main else Q(),
            Q(job_keyword_sub__overlap=query.job_keyword_sub) if query.job_keyword_sub else Q(),
        )

        # 검색어 필터링
        if query.search:
            qs = qs.filter(
                Q(job_posting_title__icontains=query.search)
                | Q(summary__icontains=query.search)
                | Q(company_id__company_name__icontains=query.search)
            )

        district_filter = Q()
        if query.city_no:
            district_filter |= Q(city_no__in=query.city_no)
        if query.district_no:
            district_filter |= Q(district_no__in=query.district_no)
        if query.town_no:
            district_filter |= Q(emd_no__in=query.town_no)

        districts = District.objects.filter(district_filter).distinct()

        # 변환 매핑 생성
        city_code_to_name = {d.city_no: d.city_name for d in districts}
        district_code_to_name = {d.district_no: d.district_name for d in districts}
        town_code_to_name = {d.emd_no: d.emd_name for d in districts}

        # JobPosting 필터링
        if query.city_no:
            qs = qs.filter(city__in=city_code_to_name.values())
        if query.district_no:
            qs = qs.filter(district__in=district_code_to_name.values())
        if query.town_no:
            qs = qs.filter(town__in=town_code_to_name.values())
        # 6. 공간 필터링 (읍면동 기준, 3km 반경)
        if query.town_no and district_filter:
            regions = District.objects.filter(district_filter).aggregate(Union("geometry"))["geometry__union"]
            if regions:
                regions_3km = regions.buffer(3000)  # 3km 버퍼
                qs = qs.filter(location__dwithin=(regions_3km, D(km=0)))

        # 7. 북마크 여부
        if current_user:
            bookmarked_qs = JobPostingBookmark.objects.filter(
                user_id=current_user.common_user_id,
                job_posting_id=OuterRef("pk"),
            )
            qs = qs.annotate(is_bookmarked=Exists(bookmarked_qs))

        # 최종 결과 필드 제한
        final_qs = qs.only(
            "job_posting_id",
            "company_id__company_name",
            "job_posting_title",
            "city",
            "district",
            "town",
            "deadline",
            "summary",
            "company_id__company_logo",
        )

        #  지역 코드 리스트 수집
        city_codes = final_qs.values_list("city", flat=True).distinct()
        district_codes = final_qs.values_list("district", flat=True).distinct()
        town_codes = final_qs.values_list("town", flat=True).distinct()

        #  District에서 지역 이름 조회
        districts = District.objects.filter(
            Q(city_name__in=city_codes) | Q(district_name__in=district_codes) | Q(emd_name__in=town_codes)
        ).distinct()

        city_name_map = {d.city_name: d.city_name for d in districts}
        district_name_map = {d.district_name: d.district_name for d in districts}
        # town_name_map = {d.emd_name: d.emd_name for d in districts} 혹시 읍면동 정보 필요할 시

        paginator = Paginator(final_qs, 20)  # 페이지당 20개
        page_number = request.GET.get("page", 1)
        try:
            page_obj = paginator.page(page_number)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        results = [
            JobPostingResultModel(
                company_name=jp.company_id.company_name,
                job_posting_id=jp.job_posting_id,
                job_posting_title=jp.job_posting_title,
                city=city_name_map.get(jp.city, jp.city),
                district=district_name_map.get(jp.district, jp.district),
                is_bookmarked=jp.is_bookmarked if hasattr(jp, "is_bookmarked") else False,
                deadline=jp.deadline,
                summary=jp.summary,
                company_logo=jp.company_id.company_logo,
            )
            for jp in page_obj.object_list  # 페이지 객체에서 아이템 가져오기
        ]

        response = JobPostingSearchResponseModel(
            results=results,
            page=page_obj.number,  # 현재 페이지 번호
            total_pages=paginator.num_pages,  # 전체 페이지 수
            total_results=paginator.count,  # 전체 결과 수
        )
        return JsonResponse(response.model_dump(), safe=False)
