import json
import uuid
from typing import List

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt, csrf_protect

from resume.models import CareerInfo, Certification, Resume
from resume.schemas import (
    CareerInfoModel,
    CertificationInfoModel,
    MyResume,
    MyResumeListOutput,
    MyResumeMixinResponse,
    ResumeCreateModel,
    ResumeListOutputModel,
    ResumeListResponseModel,
    ResumeOutputModel,
    ResumeResponseModel,
    ResumeUpdateModel,
)
from resume.serializer import (
    serialize_careers,
    serialize_certifications,
    serialize_resume_list,
)
from user.models import CommonUser, UserInfo
from user.schemas import UserInfoModel
from utils.common import get_user_from_token, get_valid_normal_user

# ------------------------
# 이력서 관련 api
# ------------------------


@method_decorator(csrf_exempt, name="dispatch")
class MyResumeListView(View):
    """
    이력서
    """

    def get(self, request: HttpRequest) -> JsonResponse:
        """
        내 이력서 리스트 조회
        """
        try:
            valid_user: CommonUser = get_user_from_token(request)
            user: UserInfo = get_valid_normal_user(valid_user)
            resumes: list[Resume] = list(Resume.objects.filter(user=user))

            resume_models: List[ResumeListOutputModel] = []
            for resume in resumes:
                resume_models.append(
                    ResumeListOutputModel(
                        job_category=resume.job_category,
                        resume_id=resume.resume_id,
                        resume_title=resume.resume_title,
                        updated_at=resume.updated_at.date(),
                    )
                )
            response = ResumeListResponseModel(
                message="Resume list loaded successfully",
                resume_list=resume_models,
            )
            return JsonResponse(response.model_dump(), status=200)
        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=400)

    def post(self, request: HttpRequest) -> JsonResponse:
        """
        새로운 이력서 등록
        """
        from pydantic_core._pydantic_core import ValidationError

        try:
            valid_user: CommonUser = get_user_from_token(request)
            user: UserInfo = get_valid_normal_user(valid_user)
            data = json.loads(request.body)
            resume_data: ResumeCreateModel = ResumeCreateModel(**data)

            with transaction.atomic():
                new_resume = create_new_resume(user, resume_data)
                career_models: list[CareerInfoModel] = (
                    resume_data.career_list if resume_data.career_list is not None else []
                )
                certification_models: list[CertificationInfoModel] = (
                    resume_data.certification_list if resume_data.certification_list is not None else []
                )
                resume_model = ResumeOutputModel(
                    resume_id=new_resume.resume_id,
                    user=UserInfoModel.model_validate(user),
                    resume_title=new_resume.resume_title,
                    job_category=new_resume.job_category,
                    education_level=new_resume.education_level,
                    school_name=new_resume.school_name,
                    education_state=new_resume.education_state,
                    introduce=new_resume.introduce,
                    career_list=career_models or [],
                    certification_list=certification_models or [],
                )
                response = ResumeResponseModel(message="Resume created successfully", resume=resume_model)
                return JsonResponse(response.model_dump(), status=201)
        except json.JSONDecodeError:  # JSON 파싱 오류 별도 처리
            return JsonResponse({"errors": "Invalid JSON format"}, status=400)
        except ValidationError as e:  # Pydantic 유효성 검사 오류 별도 처리
            return JsonResponse({"errors": e.errors()}, status=400)  # 상세 오류 반환
        except PermissionDenied as e:  # get_vaild_user에서 발생한 권한 오류 처리
            return JsonResponse({"errors": str(e)}, status=403)
        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=400)


@method_decorator(csrf_exempt, name="dispatch")
class MyResumeDetailView(View):
    """
    이력서 단일 조회 / 수정 / 삭제
    """

    def get(self, request: HttpRequest, resume_id: uuid.UUID) -> JsonResponse:
        """
        이력서 상세 조회
        """
        try:
            valid_user: CommonUser = get_user_from_token(request)
            user: UserInfo = get_valid_normal_user(valid_user)
            resume_list = (
                Resume.objects.select_related("user").filter(user=user).prefetch_related("careers", "certifications")
            ).all()
            if not resume_list:
                return JsonResponse({"error": "Not found resume data"}, status=404)
            resume = resume_list.filter(resume_id=resume_id).first()
            if not resume:
                return JsonResponse({"error": "Not found resume data"}, status=404)

            resume_list_output: list[MyResume] = serialize_resume_list(list(resume_list.all()))
            career_models: list[CareerInfoModel] = serialize_careers(list(resume.careers.all()))
            certification_models = serialize_certifications(list(resume.certifications.all()))
            resume_model: MyResumeListOutput = MyResumeListOutput(
                resume_id=resume.resume_id,
                job_category=resume.job_category,
                resume_title=resume.resume_title,
                education_level=resume.education_level,
                school_name=resume.school_name,
                education_state=resume.education_state,
                introduce=resume.introduce,
                user=UserInfoModel.model_validate(resume.user),
                career_list=career_models,
                certification_list=certification_models,
                resume_list=resume_list_output,
            )
            response = MyResumeMixinResponse(message="Resume loaded successfully", resume=resume_model)
            return JsonResponse(response.model_dump(), status=200)
        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=400)

    def patch(self, request: HttpRequest, resume_id: uuid.UUID) -> JsonResponse:
        """
        이력서 수정
        """
        try:
            valid_user: CommonUser = get_user_from_token(request)
            user: UserInfo = get_valid_normal_user(valid_user)
            data = json.loads(request.body)
            update_data = ResumeUpdateModel(**data)

            resume_to_update = (
                Resume.objects.filter(user=user, resume_id=resume_id)
                .prefetch_related("careers", "certifications")
                .first()
            )
            if not resume_to_update:
                return JsonResponse({"error": "Not found resume data"}, status=404)

            # 업데이트 및 직렬화 포함
            updated_resume = update_resume(resume_to_update, update_data)

            response = ResumeResponseModel(message="Resume updated successfully", resume=updated_resume)
            return JsonResponse(response.model_dump(), status=200)

        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=400)

    def delete(self, request: HttpRequest, resume_id: uuid.UUID) -> JsonResponse:
        """
        이력서 삭제
        """
        try:
            valid_user: CommonUser = get_user_from_token(request)
            user: UserInfo = get_valid_normal_user(valid_user)
            resume = Resume.objects.get(user_id=user, resume_id=resume_id)  # type: ignore
            resume.delete()
            return JsonResponse({"message": "Successfully deleted resume"}, status=200)
        except Resume.DoesNotExist:
            return JsonResponse({"error": "Resume not found"}, status=404)
        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=400)


def create_new_resume(user: UserInfo, resume_data: ResumeCreateModel):
    # 1. 이력서 생성
    new_resume = Resume.objects.create(
        user=user,
        resume_title=resume_data.resume_title,
        job_category=resume_data.job_category,
        education_level=resume_data.education_level,
        school_name=resume_data.school_name,
        education_state=resume_data.education_state,
        introduce=resume_data.introduce,
    )

    # 2. 경력 정보 벌크 생성
    career_list = (
        [
            CareerInfo(
                resume=new_resume,
                company_name=career.company_name,
                position=career.position,
                employment_period_start=career.employment_period_start,
                employment_period_end=career.employment_period_end,
            )
            for career in resume_data.career_list
        ]
        if resume_data.career_list
        else []
    )

    # 3. 자격증 정보 벌크 생성
    certification_list = (
        [
            Certification(
                resume=new_resume,
                certification_name=certification.certification_name,
                issuing_organization=certification.issuing_organization,
                date_acquired=certification.date_acquired,
            )
            for certification in resume_data.certification_list
        ]
        if resume_data.certification_list
        else []
    )

    # 4. 벌크 쿼리 실행
    if career_list:
        CareerInfo.objects.bulk_create(career_list)

    if certification_list:
        Certification.objects.bulk_create(certification_list)

    return new_resume


def update_resume(resume: Resume, update_data: ResumeUpdateModel) -> ResumeOutputModel:
    # 기본 정보 수정
    for field in [
        "job_category",
        "resume_title",
        "education_level",
        "school_name",
        "education_state",
        "introduce",
    ]:
        value = getattr(update_data, field, None)
        if value is not None:
            setattr(resume, field, value)
    resume.save()

    # 경력 수정
    if update_data.career_list is not None:
        resume.careers.all().delete()
        for career in update_data.career_list:
            CareerInfo.objects.create(
                resume_id=resume.resume_id,
                company_name=career.company_name,
                position=career.position,
                employment_period_start=career.employment_period_start,
                employment_period_end=career.employment_period_end,
                # type: ignore
            )

    # 자격증 수정
    if update_data.certification_list is not None:
        resume.certifications.all().delete()
        for certification in update_data.certification_list:
            Certification.objects.create(
                resume_id=resume.resume_id,
                certification_name=certification.certification_name,
                issuing_organization=certification.issuing_organization,
                date_acquired=certification.date_acquired,
            )

    updated_resume = (
        Resume.objects.filter(resume_id=resume.resume_id).prefetch_related("careers", "certifications").first()
    )

    if updated_resume is None:
        raise Resume.DoesNotExist(f"Resume with id {resume.resume_id} does not exist.")
    career_models = serialize_careers(list(updated_resume.careers.all()))
    certification_models = serialize_certifications(list(updated_resume.certifications.all()))

    return ResumeOutputModel(
        resume_id=updated_resume.resume_id,
        job_category=updated_resume.job_category,
        resume_title=updated_resume.resume_title,
        education_level=updated_resume.education_level,
        school_name=updated_resume.school_name,
        education_state=updated_resume.education_state,
        introduce=updated_resume.introduce,
        user=UserInfoModel.model_validate(updated_resume.user),
        career_list=career_models,
        certification_list=certification_models,
    )
