import json
import uuid
from typing import List

from django.contrib.gis.geos import Point
from django.db import transaction
from django.http import HttpRequest, JsonResponse
from django.views import View
from mypy.join import join_types

from job_posting.models import JobPosting, JobPostingBookmark
from job_posting.schemas import (
    BookmarkResponseModel,
    JobPostingBookmarkListItemModel,
    JobPostingBookmarkListResponseModel,
    JobPostingCreateModel,
    JobPostingDetailResponseModel,
    JobPostingListModel,
    JobPostingListResponseModel,
    JobPostingResponseModel,
    JobPostingUpdateModel,
)
from user.models import CommonUser, CompanyInfo, UserInfo
from utils.common import (
    check_and_return_company_user,
    check_and_return_normal_user,
    get_user_from_token,
)


class JobPostingListView(View):
    """
    공고 리스트 조회 API
    """

    def get(self, request: HttpRequest) -> JsonResponse:
        try:
            valid_user: CommonUser = get_user_from_token(request)
            user = None
            if valid_user:
                if valid_user.join_type == "normal":
                    user = check_and_return_normal_user(valid_user) if valid_user else None
                    postings = JobPosting.objects.select_related("company_id").all()

                elif valid_user.join_type == "company":
                    user = check_and_return_company_user(valid_user)
                    postings = JobPosting.objects.select_related("company_id").filter(company_id=user)
            else:
                postings = JobPosting.objects.select_related("company_id").all()

            bookmarked_ids: set[int] = set()
            if isinstance(user, CommonUser):
                bookmarked_ids = set(
                    JobPostingBookmark.objects.filter(user=user).values_list("job_posting_id", flat=True)
                )

            items: List[JobPostingListModel] = [
                JobPostingListModel(
                    job_posting_id=post.job_posting_id,
                    company_id=post.company_id.company_id,
                    company_name=post.company_id.company_name,
                    company_address=post.company_id.company_address,
                    job_posting_title=post.job_posting_title,
                    summary=post.summary,
                    deadline=post.deadline,
                    is_bookmarked=(post.job_posting_id in bookmarked_ids),
                )
                for post in postings
            ]
            response = JobPostingListResponseModel(
                message="공고 리스트를 성공적으로 불러왔습니다.",
                data=items,
            )
            return JsonResponse(response.model_dump(), status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


class JobPostingDetailView(View):
    """
    공고 상세 조회 / 생성 / 수정 / 삭제 API
    """

    def get(self, request: HttpRequest, job_posting_id: uuid.UUID) -> JsonResponse:
        try:
            post = JobPosting.objects.select_related("company_id").filter(job_posting_id=job_posting_id).first()
            if not post:
                return JsonResponse({"error": "공고를 찾을 수 없습니다."}, status=404)

            valid_user: CommonUser = get_user_from_token(request)
            user = None
            if valid_user:
                if valid_user.join_type == "normal":
                    user = check_and_return_normal_user(valid_user)
                elif valid_user.join_type == "company":
                    user = check_and_return_company_user(valid_user)
            is_bookmarked = (
                isinstance(user, UserInfo)
                and JobPostingBookmark.objects.filter(user=valid_user, job_posting=post).exists()
            )

            detail = JobPostingResponseModel(
                job_posting_id=post.job_posting_id,
                company_id=post.company_id.company_id,
                company_logo=post.company_id.company_logo,
                company_name=post.company_id.company_name,
                manager_phone_number=post.company_id.manager_phone_number,
                manager_name=post.company_id.manager_name,
                job_posting_title=post.job_posting_title,
                address=post.address,
                city=post.city,
                district=post.district,
                town=post.town,
                location=(post.location.x, post.location.y),
                work_time_start=post.work_time_start,
                work_time_end=post.work_time_end,
                posting_type=post.posting_type,
                employment_type=post.employment_type,
                work_experience=post.work_experience,
                job_keyword_main=post.job_keyword_main,
                job_keyword_sub=post.job_keyword_sub,
                number_of_positions=post.number_of_positions,
                education=post.education,
                deadline=post.deadline,
                time_discussion=post.time_discussion,
                day_discussion=post.day_discussion,
                work_day=post.work_day,
                salary_type=post.salary_type,
                salary=post.salary,
                summary=post.summary,
                content=post.content,
                is_bookmarked=is_bookmarked,
            )
            response = JobPostingDetailResponseModel(
                message="공고를 성공적으로 불러왔습니다.",
                job_posting=detail,
            )
            return JsonResponse(response.model_dump(), status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    def post(self, request: HttpRequest) -> JsonResponse:
        try:
            valid_user: CommonUser = get_user_from_token(request)
            company: CompanyInfo = check_and_return_company_user(valid_user)
            if not (company):
                return JsonResponse(
                    {"error": "기업 사용자만 공고를 등록할 수 있습니다."},
                    status=403,
                )

            data = json.loads(request.body)
            payload = JobPostingCreateModel(**data)

            # location을 Point로 변환
            location = Point(payload.location[0], payload.location[1])

            with transaction.atomic():
                post = JobPosting.objects.create(
                    company_id=company,
                    job_posting_title=payload.job_posting_title,
                    address=payload.address,
                    city=payload.city,
                    district=payload.district,
                    town=payload.town,
                    location=location,
                    work_time_start=payload.work_time_start,
                    work_time_end=payload.work_time_end,
                    posting_type=payload.posting_type,
                    employment_type=payload.employment_type,
                    work_experience=payload.work_experience,
                    job_keyword_main=payload.job_keyword_main,
                    job_keyword_sub=payload.job_keyword_sub,
                    number_of_positions=payload.number_of_positions,
                    education=payload.education,
                    deadline=payload.deadline,
                    time_discussion=payload.time_discussion,
                    day_discussion=payload.day_discussion,
                    work_day=payload.work_day,
                    salary_type=payload.salary_type,
                    salary=payload.salary,
                    summary=payload.summary,
                    content=payload.content or "",
                )

            detail = JobPostingResponseModel(
                job_posting_id=post.job_posting_id,
                company_id=post.company_id.company_id,
                company_logo=post.company_id.company_logo,
                company_name=post.company_id.company_name,
                manager_phone_number=post.company_id.manager_phone_number,
                manager_name=post.company_id.manager_name,
                job_posting_title=post.job_posting_title,
                address=post.address,
                city=post.city,
                district=post.district,
                town=post.town,
                location=(post.location.x, post.location.y),
                work_time_start=post.work_time_start,
                work_time_end=post.work_time_end,
                posting_type=post.posting_type,
                employment_type=post.employment_type,
                work_experience=post.work_experience,
                job_keyword_main=post.job_keyword_main,
                job_keyword_sub=post.job_keyword_sub,
                number_of_positions=post.number_of_positions,
                education=post.education,
                deadline=post.deadline,
                time_discussion=post.time_discussion,
                day_discussion=post.day_discussion,
                work_day=post.work_day,
                salary_type=post.salary_type,
                salary=post.salary,
                summary=post.summary,
                content=post.content,
                is_bookmarked=False,
            )
            response = JobPostingDetailResponseModel(
                message="공고가 성공적으로 등록되었습니다.",
                job_posting=detail,
            )
            return JsonResponse(response.model_dump(), status=201)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    def patch(self, request: HttpRequest, job_posting_id: uuid.UUID) -> JsonResponse:
        try:
            valid_user: CommonUser = get_user_from_token(request)
            company: CompanyInfo = check_and_return_company_user(valid_user)
            if not (company):
                return JsonResponse(
                    {"error": "기업 사용자만 공고를 수정할 수 있습니다."},
                    status=403,
                )

            post = JobPosting.objects.filter(job_posting_id=job_posting_id).first()
            if not post or post.company_id != company:
                return JsonResponse(
                    {"error": "수정 권한이 없거나 공고를 찾을 수 없습니다."},
                    status=403,
                )

            data = json.loads(request.body)
            payload = JobPostingUpdateModel(**data)

            # location이 있으면 Point로 변환
            if payload.location:
                location = Point(payload.location[0], payload.location[1])
                post.location = location

            for field, value in payload.model_dump(exclude_unset=True).items():
                if field == "location":
                    continue
                setattr(post, field, value)
            post.save()

            is_bookmarked = False
            if isinstance(company, CommonUser):
                is_bookmarked = JobPostingBookmark.objects.filter(user=user, job_posting=post).exists()

            detail = JobPostingResponseModel(
                job_posting_id=post.job_posting_id,
                company_id=post.company_id.company_id,
                job_posting_title=post.job_posting_title,
                address=post.address,
                city=post.city,
                district=post.district,
                town=post.town,
                location=(post.location.x, post.location.y),
                work_time_start=post.work_time_start,
                work_time_end=post.work_time_end,
                posting_type=post.posting_type,
                employment_type=post.employment_type,
                work_experience=post.work_experience,
                job_keyword_main=post.job_keyword_main,
                job_keyword_sub=post.job_keyword_sub,
                number_of_positions=post.number_of_positions,
                education=post.education,
                deadline=post.deadline,
                time_discussion=post.time_discussion,
                day_discussion=post.day_discussion,
                work_day=post.work_day,
                salary_type=post.salary_type,
                salary=post.salary,
                summary=post.summary,
                content=post.content,
                is_bookmarked=is_bookmarked,
            )
            response = JobPostingDetailResponseModel(
                message="공고가 성공적으로 수정되었습니다.",
                job_posting=detail,
            )
            return JsonResponse(response.model_dump(), status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    def delete(self, request: HttpRequest, job_posting_id: uuid.UUID) -> JsonResponse:
        try:
            valid_user: CommonUser = get_user_from_token(request)
            company: CompanyInfo = check_and_return_company_user(valid_user)
            if not (company):
                return JsonResponse(
                    {"error": "기업 사용자만 공고를 삭제할 수 있습니다."},
                    status=403,
                )

            post = JobPosting.objects.filter(job_posting_id=job_posting_id).first()
            if not post or post.company_id != company:
                return JsonResponse(
                    {"error": "삭제 권한이 없거나 공고를 찾을 수 없습니다."},
                    status=403,
                )

            post.delete()
            response = BookmarkResponseModel(message="공고가 성공적으로 삭제되었습니다.")
            return JsonResponse(response.model_dump(), status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


class JobPostingBookmarkView(View):
    """
    공고 북마크 등록 / 삭제 / 조회 API
    """

    def get(self, request: HttpRequest) -> JsonResponse:
        try:
            valid_user: CommonUser = get_user_from_token(request)
            current_user = check_and_return_normal_user(valid_user) if valid_user else None
            if not isinstance(current_user, CommonUser):
                return JsonResponse({"error": "인증된 사용자만 접근할 수 있습니다."}, status=403)

            bookmarks = JobPostingBookmark.objects.select_related("job_posting__company_id").filter(user=current_user)

            items = [
                JobPostingBookmarkListItemModel(
                    job_posting_id=b.job_posting.job_posting_id,
                    job_posting_title=b.job_posting.job_posting_title,
                    company_name=b.job_posting.company_id.company_name,
                    summary=b.job_posting.summary,
                    deadline=b.job_posting.deadline,
                )
                for b in bookmarks
            ]
            response = JobPostingBookmarkListResponseModel(
                message="북마크 목록을 성공적으로 불러왔습니다.",
                data=items,
            )
            return JsonResponse(response.model_dump(), status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    def post(self, request: HttpRequest, job_posting_id: uuid.UUID) -> JsonResponse:
        try:
            valid_user: CommonUser = get_user_from_token(request)
            current_user = check_and_return_normal_user(valid_user) if valid_user else None
            if not isinstance(current_user, UserInfo):
                return JsonResponse({"error": "인증된 사용자만 접근할 수 있습니다."}, status=403)

            post = JobPosting.objects.filter(job_posting_id=job_posting_id).first()
            if not post:
                return JsonResponse({"error": "공고를 찾을 수 없습니다."}, status=404)

            _, created = JobPostingBookmark.objects.get_or_create(user=valid_user, job_posting=post)
            response = BookmarkResponseModel(
                message=("북마크가 등록되었습니다." if created else "이미 북마크한 공고입니다.")
            )
            return JsonResponse(response.model_dump(), status=201 if created else 200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    def delete(self, request: HttpRequest, job_posting_id: uuid.UUID) -> JsonResponse:
        try:
            valid_user: CommonUser = get_user_from_token(request)
            current_user = check_and_return_normal_user(valid_user) if valid_user else None
            if not isinstance(current_user, UserInfo):
                return JsonResponse({"error": "인증된 사용자만 접근할 수 있습니다."}, status=403)

            bookmark = JobPostingBookmark.objects.filter(user=valid_user, job_posting_id=job_posting_id).first()
            if not bookmark:
                response = BookmarkResponseModel(message="해당 공고는 북마크되어 있지 않습니다.")
                return JsonResponse(response.model_dump(), status=404)

            bookmark.delete()
            response = BookmarkResponseModel(message="북마크가 삭제되었습니다.")
            return JsonResponse(response.model_dump(), status=200)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
