import json
import uuid

from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from job_posting.models import JobPosting, JobPostingBookmark
from resume.models import Resume, Submission
from resume.schemas import (
    CareerInfoModel,
    CertificationInfoModel,
    JobpostingGetListModel,
    JobpostingListOutputModel,
    SnapshotResumeModel,
    SubmissionCompanyDetailModel,
    SubmissionCompanyGetListInfoModel,
    SubmissionCompanyGetListOutputModel,
    SubmissionCompanyOutputDetailModel,
    SubmissionDetailResponseModel,
    SubmissionListResponseModel,
    SubmissionMemoResponseModel,
    SubmissionMemoUpdateModel,
    SubmissionModel,
    SubmissionOutputModel,
)
from resume.serializer import (
    serialize_careers,
    serialize_certifications,
    serialize_submissions,
)
from user.models import CommonUser, CompanyInfo, UserInfo
from utils.common import (
    check_and_return_company_user,
    check_and_return_normal_user,
    get_user_from_token,
)

# ------------------------
# 지원 관련 api
# ------------------------


@method_decorator(csrf_exempt, name="dispatch")
class SubmissionListView(View):
    """
    지원한 공고 리스트 API (유저)
    """

    def get(self, request: HttpRequest) -> JsonResponse:
        """
        지원한 공고 리스트 조회
        """
        try:
            valid_user: CommonUser = get_user_from_token(request)
            user: UserInfo = check_and_return_normal_user(valid_user)
            submissions: list[Submission] = list(Submission.objects.filter(user=user).all())

            submission_model = serialize_submissions(submissions)

            response = SubmissionListResponseModel(
                message="Successfully loaded submission list",
                submission_list=submission_model,
            )

            return JsonResponse(response.model_dump(), status=200)
        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=400)

    def post(self, request: HttpRequest) -> JsonResponse:
        """
        공고 지원 (유저)
        """
        try:
            valid_user: CommonUser = get_user_from_token(request)
            user: UserInfo = check_and_return_normal_user(valid_user)
            data = json.loads(request.body)
            job_posting_id = data.get("job_posting_id")
            resume_id = data.get("resume_id")

            job_posting = get_object_or_404(JobPosting, pk=job_posting_id)
            resume = Resume.objects.filter(resume_id=resume_id).prefetch_related("careers", "certifications").first()
            if job_posting is None:
                return JsonResponse({"errors": "Not founded job_posting data"}, status=404)
            if resume is None:
                return JsonResponse({"errors": "Not founded resume data"}, status=404)

            # Submission 생성
            submission = save_submission(job_posting=job_posting, resume=resume, user=user)

            job_posting_model = JobpostingListOutputModel(
                job_posting_id=job_posting.job_posting_id,
                city=job_posting.city,
                district=job_posting.district,
                town=job_posting.town,
                company_name=job_posting.company_id.company_name,
                company_address=job_posting.company_id.company_address,
                job_posting_title=job_posting.job_posting_title,
                summary=job_posting.summary,
                deadline=job_posting.deadline,
                is_bookmarked=(
                    True if JobPostingBookmark.objects.filter(job_posting_id=job_posting).exists() else False
                ),
            )

            submission_model = SubmissionModel(
                submission_id=submission.submission_id,
                job_posting=job_posting_model,
                snapshot_resume=SnapshotResumeModel.model_validate(submission.snapshot_resume),
                memo=submission.memo,
                is_read=submission.is_read,
                created_at=submission.created_at.date(),
            )

            response = SubmissionDetailResponseModel(
                message="Successfully create new submission",
                submission=submission_model,
            )
            return JsonResponse(response.model_dump(mode="json"), status=201)

        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=400)


# ------------------------
# 지원 관련 상세 api
# ------------------------


@method_decorator(csrf_protect, name="dispatch")
class SubmissionDetailView(View):
    """
    지원 공고 상세
    """

    def get(self, request: HttpRequest, submission_id: uuid.UUID) -> JsonResponse:
        """
        상세 데이터 조회
        """
        try:
            valid_user: CommonUser = get_user_from_token(request)
            user: UserInfo = check_and_return_normal_user(valid_user)

            submission: Submission = Submission.objects.get(user=user, submission_id=submission_id)
            if submission is None:
                return JsonResponse({"errors": "Not found submission data"}, status=404)
            job_posting_model = JobpostingListOutputModel(
                job_posting_id=submission.job_posting.job_posting_id,
                city=submission.job_posting.city,
                district=submission.job_posting.district,
                town=submission.job_posting.town,
                company_name=submission.job_posting.company_id.company_name,
                company_address=submission.job_posting.company_id.company_address,
                summary=submission.job_posting.summary,
                deadline=submission.job_posting.deadline,
                job_posting_title=submission.job_posting.job_posting_title,
                is_bookmarked=JobPostingBookmark.objects.filter(user_id=submission.user.user_id).exists(),
            )
            submission_model = SubmissionModel(
                submission_id=submission.submission_id,
                snapshot_resume=submission.snapshot_resume,
                job_posting=job_posting_model,
                memo=submission.memo,
                is_read=submission.is_read,
                created_at=submission.created_at.date(),
            )

            response = SubmissionDetailResponseModel(
                message="Successfully loaded submission data",
                submission=submission_model,
            )
            return JsonResponse(response.model_dump(), status=200)

        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=400)

    def delete(self, request: HttpRequest, submission_id: uuid.UUID) -> JsonResponse:
        """
        지원공고 삭제
        """
        try:
            valid_user: CommonUser = get_user_from_token(request)
            user: UserInfo = check_and_return_normal_user(valid_user)
            submission: Submission = Submission.objects.get(submission_id=submission_id)
            if submission is None:
                return JsonResponse({"errors": "Not found submission data"}, status=404)
            submission.delete()
            return JsonResponse({"message": "Successfully data deleted"}, status=200)
        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=400)


@method_decorator(csrf_protect, name="dispatch")
class SubmissionMemoView(View):
    """
    memo update 및 delete 뷰
    """

    def patch(self, request: HttpRequest, submission_id: uuid.UUID) -> JsonResponse:
        """
        memo 수정
        """
        try:
            valid_user: CommonUser = get_user_from_token(request)
            user: UserInfo = check_and_return_normal_user(valid_user)
            data = json.loads(request.body)
            update_data = SubmissionMemoUpdateModel(memo=data.get("memo", ""))

            submission: Submission = Submission.objects.get(submission_id=submission_id)
            if submission is None:
                return JsonResponse({"errors": "Not found submission data"}, status=404)
            if update_data is not None:
                submission.memo = str(update_data.memo)
                submission.save()

            response = SubmissionMemoResponseModel(message="Successfully updated memo", memo=submission.memo)
            return JsonResponse(response.model_dump(), status=200)
        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=400)

    def delete(self, request: HttpRequest, submission_id: uuid.UUID) -> JsonResponse:
        """
        memo 삭제
        """
        try:
            valid_user: CommonUser = get_user_from_token(request)
            user: UserInfo = check_and_return_normal_user(valid_user)
            submission = Submission.objects.get(user=user, submission_id=submission_id)
            if submission is not None:
                submission.memo = None
                submission.save()
            else:
                return JsonResponse({"errors": "Not found submission data"}, status=404)

            return JsonResponse({"message": "Successfully deleted submission memo"}, status=200)
        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=400)


class SubmissionCompanyListView(View):
    """
    기업 유저 지원자 목록 조회
    """

    def get(self, request: HttpRequest) -> JsonResponse:
        """
        공고 제목 및 지원서 목록 리스트 조회
        """
        try:
            valid_user: CommonUser = get_user_from_token(request)
            user: CompanyInfo = check_and_return_company_user(valid_user)
            submission_list = Submission.objects.filter(job_posting__company_id=user.company_id).all()
            job_posting_list_model: list[JobpostingGetListModel] = [
                JobpostingGetListModel.model_validate(submission.job_posting) for submission in submission_list
            ]
            submission_list_model: list[SubmissionCompanyGetListInfoModel] = [
                SubmissionCompanyGetListInfoModel(
                    submission_id=submission.submission_id,
                    job_posting_id=submission.job_posting.job_posting_id,
                    name=submission.user.name,
                    summary=submission.job_posting.summary,
                    is_read=submission.is_read,
                    created_at=submission.created_at.date(),
                    resume_title=submission.snapshot_resume["resume_title"],
                )
                for submission in submission_list
            ]

            response = SubmissionCompanyGetListOutputModel(
                message="Successfully loaded submission_list",
                job_posting_list=job_posting_list_model,
                submission_list=submission_list_model,
            )

            return JsonResponse(response.model_dump(), status=200)
        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=400)


class SubmissionCompanyDetialView(View):
    """
    기업회원 지원자 이력서 조회
    """

    def get(self, request: HttpRequest, submission_id: uuid.UUID) -> JsonResponse:
        try:
            valid_user: CommonUser = get_user_from_token(request)
            user: CompanyInfo = check_and_return_company_user(valid_user)
            submission = Submission.objects.get(submission_id=submission_id)
            if submission is None:
                return JsonResponse({"errors": "Not found submission data"}, status=404)
            submission.is_read = True
            submission.save()

            submission_model = SubmissionCompanyOutputDetailModel(
                job_category=submission.snapshot_resume["job_category"],
                name=submission.user.name,
                resume_title=submission.snapshot_resume["resume_title"],
                education_state=submission.snapshot_resume["education_state"],
                education_level=submission.snapshot_resume["education_level"],
                school_name=submission.snapshot_resume["school_name"],
                introduce=submission.snapshot_resume["introduce"],
                career_list=submission.snapshot_resume["career_list"],
                certification_list=submission.snapshot_resume["certification_list"],
            )

            response = SubmissionCompanyDetailModel(
                message="Successfully loaded submission data",
                submission=submission_model,
            )
            return JsonResponse(response.model_dump(), status=200)

        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=400)


def save_submission(job_posting: JobPosting, user: UserInfo, resume: Resume) -> Submission:
    # 이력서 정보 dict로 직렬화
    career_model: list[CareerInfoModel] = serialize_careers(list(resume.careers.all()))
    certification_model: list[CertificationInfoModel] = serialize_certifications(list(resume.certifications.all()))

    resume_model = SubmissionOutputModel(
        job_category=resume.job_category,
        resume_title=resume.resume_title,
        education_state=resume.education_state,
        school_name=resume.school_name,
        education_level=resume.education_level,
        introduce=resume.introduce,
        career_list=career_model,
        certification_list=certification_model,
    )
    submission = Submission.objects.create(
        job_posting=job_posting,
        user=user,
        snapshot_resume=resume_model.model_dump(mode="json"),
    )
    return submission
