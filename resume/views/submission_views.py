import json
import uuid
from http.client import responses

from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from job_posting.models import JobPosting
from resume.models import Resume, Submission
from resume.schemas import (
    CareerInfoModel,
    CertificationInfoModel,
    JobpostingListOutputModel,
    ResumeOutputModel,
    SubmissionDetailResponseModel,
    SubmissionListResponseModel,
    SubmissionMemoUpdateModel,
    SubmissionModel,
)
from resume.serializer import (
    serialize_careers,
    serialize_certifications,
    serialize_submissions,
)
from user.models import UserInfo
from user.schemas import UserInfoModel
from utils.common import get_vaild_nomal_user

# ------------------------
# 지원 관련 api
# ------------------------


class SubmissionListView(View):
    """
    지원한 공고 리스트 API (유저)
    """

    def get(self, request: HttpRequest) -> JsonResponse:
        """
        지원한 공고 리스트 조회
        """
        try:
            token = request.user
            user = get_vaild_nomal_user(token)
            submissions: list[Submission] = list(
                Submission.objects.filter(user=user).all()
            )

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
            token = request.user
            user = get_vaild_nomal_user(token)
            data = json.loads(request.body)
            job_posting_id = data.get("job_posting_id")
            resume_id = data.get("resume_id")

            job_posting = get_object_or_404(JobPosting, pk=job_posting_id)
            resume = (
                Resume.objects.filter(resume_id=resume_id)
                .prefetch_related("careers", "certifications")
                .first()
            )
            if resume is None:
                return JsonResponse(
                    {"errors": "Not founded resume data"}, status=404
                )

            # Submission 생성
            submission = save_submission(
                job_posting=job_posting, resume=resume, user=user
            )

            job_posting_model = JobpostingListOutputModel.model_validate(
                job_posting
            )

            submission_model = SubmissionModel(
                submission_id=submission.submission_id,
                job_posting=job_posting_model,
                snapshot_resume=ResumeOutputModel.model_validate(
                    submission.snapshot_resume
                ),
                memo=submission.memo,
                is_read=submission.is_read,
                created_at=submission.created_at,
            )

            response = SubmissionDetailResponseModel(
                message="Successfully create new submission",
                submission=submission_model,
            )
            return JsonResponse(response.model_dump(), status=201)

        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=400)


# ------------------------
# 지원 관련 상세 api
# ------------------------


class SubmissionDetailView(View):
    """
    지원 공고 상세
    """

    def get(
        self, request: HttpRequest, submission_id: uuid.UUID
    ) -> JsonResponse:
        """
        상세 데이터 조회
        """
        try:
            token = request.user
            user = get_vaild_nomal_user(token)

            submission: Submission = Submission.objects.get(
                submission_id=submission_id
            )
            if submission is None:
                return JsonResponse(
                    {"errors": "Not found submission data"}, status=404
                )
            submission_model = SubmissionModel.model_validate(submission)

            response = SubmissionDetailResponseModel(
                message="Successfully loaded submission data",
                submission=submission_model,
            )
            return JsonResponse(response.model_dump(), status=200)

        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=400)

    def patch(
        self, request: HttpRequest, submission_id: uuid.UUID
    ) -> JsonResponse:
        try:
            token = request.user
            user = get_vaild_nomal_user(token)
            data = json.loads(request.body)
            update_data = SubmissionMemoUpdateModel(memo=data.get("memo", ""))

            submission: Submission = Submission.objects.get(
                submission_id=submission_id
            )
            if submission is None:
                return JsonResponse(
                    {"errors": "Not found submission data"}, status=404
                )
            submission.memo = update_data.memo
            submission.save()
            submission_model = SubmissionModel.model_validate(submission)

            response = SubmissionDetailResponseModel(
                message="Successfully updated memo", submission=submission_model
            )
            return JsonResponse(response.model_dump(), status=200)

        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=400)

    def delete(
        self, request: HttpRequest, submission_id: uuid.UUID
    ) -> JsonResponse:
        """
        지원공고 삭제
        """
        try:
            token = request.user
            user = get_vaild_nomal_user(token)
            submission: Submission = Submission.objects.get(
                submission_id=submission_id
            )
            if submission is None:
                return JsonResponse(
                    {"errors": "Not found submission data"}, status=404
                )
            submission.delete()
            return JsonResponse(
                {"message": "Successfully data deleted"}, status=200
            )
        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=400)


def save_submission(
    job_posting: JobPosting, user: UserInfo, resume: Resume
) -> Submission:
    # 이력서 정보 dict로 직렬화
    career_model: list[CareerInfoModel] = serialize_careers(
        list(resume.careers.all())
    )
    certification_model: list[CertificationInfoModel] = (
        serialize_certifications(list(resume.certifications.all()))
    )
    resume_dict = {
        "resume_id": str(resume.resume_id),
        "user": UserInfoModel.model_validate(user).model_dump(),
        "job_category": resume.job_category,
        "resume_title": resume.resume_title,
        "education_level": resume.education_level,
        "school_name": resume.school_name,
        "education_state": resume.education_state,
        "introduce": resume.introduce,
        "career_list": career_model,
        "certification_list": certification_model,
    }
    resume_model = ResumeOutputModel.model_validate(resume_dict)
    submission = Submission.objects.create(
        job_posting=job_posting,
        user=user,
        snapshot_resume=resume_model,
    )
    return submission
