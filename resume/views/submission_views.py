import json
import uuid
from typing import List

from django.db import transaction
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect

from job_posting.models import JobPosting
from resume.models import CareerInfo, Certification, Resume, Submission
from resume.schemas import (
    CareerInfoModel,
    CertificationInfoModel,
    JobpostingListOutputModel,
    ResumeCreateModel,
    ResumeListResponseModel,
    ResumeModel,
    ResumeResponseModel,
    ResumeUpdateModel,
    SubmissionListResponseModel,
    SubmissionModel,
)
from user.models import UserInfo
from user.schemas import UserInfoModel


# ------------------------
# serializer (추후 분리 예정)
# ------------------------
def serialize_careers(careers: List[CareerInfo]) -> List[CareerInfoModel]:
    return [
        CareerInfoModel(
            company_name=career.company_name,
            position=career.position,
            employment_period_start=career.employment_period_start,
            employment_period_end=career.employment_period_end,
        )
        for career in careers
    ]


def serialize_certifications(
    certifications: List[Certification],
) -> List[CertificationInfoModel]:
    return [
        CertificationInfoModel(
            certification_name=certification.certification_name,
            issuing_organization=certification.issuing_organization,
            date_acquired=certification.date_acquired,
        )
        for certification in certifications
    ]


def serialize_submissions(
    submissions: List[Submission],
) -> List[SubmissionModel]:
    result = []
    for submission in submissions:
        resume_dict = submission.snapshot_resume

        # user 정보 변환
        user_info = resume_dict.get("user")
        user_model = (
            UserInfoModel.model_validate(user_info) if user_info else None
        )

        # career_list 변환
        career_list = [
            CareerInfoModel.model_validate(career)
            for career in resume_dict.get("career_list", [])
        ]
        # certification_list 변환
        certification_list = [
            CertificationInfoModel.model_validate(cert)
            for cert in resume_dict.get("certification_list", [])
        ]

        # ResumeModel 생성
        resume_model = ResumeModel(
            resume_id=resume_dict.get("resume_id"),
            user=user_model,
            job_category=resume_dict.get("job_category", ""),
            resume_title=resume_dict.get("resume_title", ""),
            education_level=resume_dict.get("education_level", ""),
            school_name=resume_dict.get("school_name", ""),
            education_state=resume_dict.get("education_state", ""),
            introduce=resume_dict.get("introduce", ""),
            career_list=career_list,
            certification_list=certification_list,
        )

        # job_posting 변환
        job_posting_model = JobpostingListOutputModel.model_validate(
            submission.job_posting
        )

        # SubmissionModel 생성
        result.append(
            SubmissionModel(
                submission_id=submission.submission_id,
                job_posting=job_posting_model,
                resume=resume_model,
                memo=submission.memo,
                is_read=submission.is_read,
                created_at=submission.created_at,
            )
        )
    return result


# ------------------------
# 지원 관련 api
# ------------------------


class SubmissionView(View):
    """
    공고 지원 API
    """

    def get(self, request: HttpRequest) -> JsonResponse:
        """
        지원한 공고 리스트 조회
        """
        try:
            user_id = request.user.id  # 토큰 형식 정해지면 수정
            submissions: List[Submission] = (
                Submission.objects.select_related("submissions_job_posting")
                .filter(resume__user_id=user_id)
                .all()
            )
            submission_models = serialize_submissions(submissions)
            response = SubmissionListResponseModel(
                message="Submissions loaded successfully",
                submission_list=submission_models,
            )
            return JsonResponse(response.model_dump(), status=200)
        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=400)

    def post(self, request: HttpRequest) -> JsonResponse:
        """
        지원 공고 등록
        """
        try:
            data = json.loads(request.body)
            job_posting_id = data.get("job_posting_id")
            resume_id = data.get("resume_id")
            memo = data.get("memo", "")
            user = request.user

            job_posting = get_object_or_404(JobPosting, pk=job_posting_id)
            resume = get_object_or_404(Resume, pk=resume_id)

            career_qs = CareerInfo.objects.filter(resume=resume)
            certification_qs = Certification.objects.filter(resume=resume)

            career_list = serialize_careers(list(career_qs))
            certification_list = serialize_certifications(
                list(certification_qs)
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
                "career_list": career_list,
                "certification_list": certification_list,
            }

            # Submission 생성
            submission = Submission.objects.create(
                job_posting=job_posting,
                user=user,
                snapshot_resume=resume_dict,
                memo=memo,
            )

            job_posting_model = JobpostingListOutputModel.model_validate(
                job_posting
            )
            resume_model = ResumeModel.model_validate(resume_dict)

            submission_model = SubmissionModel(
                submission_id=submission.submission_id,
                job_posting=job_posting_model,
                resume=resume_model,
                memo=submission.memo,
                is_read=submission.is_read,
                created_at=submission.created_at,
            )

            return JsonResponse(submission_model.model_dump(), status=201)

        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=400)


def save_submission(
    job_posting: JobPosting, user: UserInfo, resume: Resume
) -> Submission:
    # 이력서 정보 dict로 직렬화
    career_list = list(CareerInfo.objects.filter(resume=resume).values())
    certification_list = list(
        Certification.objects.filter(resume=resume).values()
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
        "career_list": career_list,
        "certification_list": certification_list,
    }
    submission = Submission.objects.create(
        job_posting=job_posting,
        user=user,
        snapshot_resume=resume_dict,
    )
    return submission
