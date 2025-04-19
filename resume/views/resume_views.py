import json
import uuid
from typing import List

from django.db import transaction
from django.http import HttpRequest, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect

from resume.models import CareerInfo, Certification, Resume, Submission
from resume.schemas import (
    CareerInfoModel,
    CertificationInfoModel,
    ResumeCreateModel,
    ResumeListResponseModel,
    ResumeModel,
    ResumeResponseModel,
    ResumeUpdateModel,
)

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


# ------------------------
# 이력서 관련 api
# ------------------------


@method_decorator(csrf_protect, name="dispatch")
class MyResumeListView(View):
    """
    이력서
    """

    def get(self, request: HttpRequest) -> JsonResponse:
        """
        내 이력서 리스트 조회
        """
        try:
            user = request.user  # 토큰 정보에 따라 수정
            resumes = (
                Resume.objects.filter(user=user)
                .select_related("resumes")
                .prefetch_related("careers", "certifications")
            )

            resume_models: List[ResumeModel] = []
            for resume in resumes:
                careers = serialize_careers(list(resume.careers.all()))
                certifications = serialize_certifications(
                    list(resume.certifications.all())
                )
                resume_models.append(
                    ResumeModel(
                        user=resume.user,
                        resume_id=resume.resume_id,
                        resume_title=resume.resume_title,
                        education_level=resume.education_level,
                        school_name=resume.school_name,
                        education_state=resume.education_state,
                        introduce=resume.introduce,
                        career_list=careers,
                        certification_list=certifications,
                    )
                )

            response = ResumeListResponseModel(
                message="Resume list loaded successfully",
                resume_list=resume_models,
            )
            return JsonResponse(response.model_dump(), status=200)
        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=400)


@method_decorator(csrf_protect, name="dispatch")
class MyResumeDetailView(View):
    """
    이력서 단일 조회 / 생성 / 수정 / 삭제
    """

    def get(self, request: HttpRequest, resume_id: uuid.UUID) -> JsonResponse:
        # TODO Resume user 파라미터 확인
        try:
            user = request.user
            resume = (
                Resume.objects.filter(user_id=user, resume_id=resume_id)  # type: ignore
                .prefetch_related("careers", "certifications")
                .first()
            )
            if not resume:
                return JsonResponse({"error": "Resume not found"}, status=404)

            career_models = serialize_careers(list(resume.careers.all()))
            certification_models = serialize_certifications(
                list(resume.certifications.all())
            )
            resume_model = ResumeModel(
                resume_id=resume.resume_id,
                job_category=resume.job_category,
                resume_title=resume.resume_title,
                education_level=resume.education_level,
                school_name=resume.school_name,
                education_state=resume.education_state,
                introduce=resume.introduce,
                career_list=career_models,
                certification_list=certification_models,
            )
            response = ResumeResponseModel(
                message="Resume loaded successfully", resume=resume_model
            )
            return JsonResponse(response.model_dump(), status=200)
        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=400)

    def post(self, request: HttpRequest) -> JsonResponse:
        """
        새로운 이력서 등록
        """
        try:
            user = request.user  # 토큰 저장 방식에 따라 바뀜
            data = json.loads(request.body)
            resume_data = ResumeCreateModel(**data)

            with transaction.atomic():
                new_resume = Resume.objects.create(  # type: ignore
                    user=user,
                    resume_title=resume_data.resume_title,
                    job_category=resume_data.job_category,
                    education_level=resume_data.education_level,
                    school_name=resume_data.school_name,
                    education_state=resume_data.education_state,
                    introduce=resume_data.introduce,
                )

                for career in resume_data.career_list:
                    CareerInfo.objects.create(  # type: ignore
                        resume=new_resume,
                        company_name=career.company_name,
                        position=career.position,
                        employment_period_start=career.employment_period_start,
                        employment_period_end=career.employment_period_end,
                    )
                for certification in resume_data.certification_list:
                    Certification.objects.create(
                        resume=new_resume,
                        certification_name=certification.certification_name,
                        issuing_organization=certification.issuing_organization,
                        date_acquired=certification.date_acquired,
                    )
                career_models = serialize_careers(
                    list(new_resume.careers.all())
                )
                certification_models = serialize_certifications(
                    list(new_resume.certifications.all())
                )
                resume_model = ResumeModel(
                    resume_id=new_resume.resume_id,
                    resume_title=new_resume.resume_title,
                    job_category=new_resume.job_category,
                    education_level=new_resume.education_level,
                    school_name=new_resume.school_name,
                    education_state=new_resume.education_state,
                    introduce=new_resume.introduce,
                    career_list=career_models,
                    certification_list=certification_models,
                )
                response = ResumeResponseModel(
                    message="Resume created successfully", resume=resume_model
                )
                return JsonResponse(response.model_dump(), status=201)

        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=400)


@method_decorator(csrf_protect, name="dispatch")
class MyResumeDetailView(View):
    """
    이력서 단일 조회 / 수정 / 삭제
    """

    def get(self, request: HttpRequest, resume_id: uuid.UUID) -> JsonResponse:
        """
        이력서 상세 조회
        """
        try:
            user = request.user
            resume = (
                Resume.objects.filter(user_id=user, resume_id=resume_id)
                .prefetch_related("careers", "certifications")
                .first()
            )
            if not resume:
                return JsonResponse({"error": "Resume not found"}, status=404)

            career_models = serialize_careers(resume.careers.all())
            resume_model = ResumeModel(
                resume_id=resume.resume_id,
                job_category=resume.job_category,
                resume_title=resume.resume_title,
                education_level=resume.education_level,
                school_name=resume.schoolname,
                education_state=resume.education_state,
                introduce=resume.introduce,
                career_list=career_models,
            )
            response = ResumeResponseModel(
                message="Resume loaded successfully", resume=resume_model
            )
            return JsonResponse(response.model_dump(), status=200)
        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=400)

    def patch(self, request: HttpRequest, resume_id: uuid.UUID) -> JsonResponse:
        """
        이력서 수정
        """
        try:
            data = json.loads(request.body)
            update_data = ResumeUpdateModel(**data)
            user = request.user

            resume = (
                Resume.objects.filter(user_id=user, resume_id=resume_id)  # type: ignore
                .prefetch_related("careers", "certifications")
                .first()
            )
            if not resume:
                return JsonResponse({"error": "Resume not found"}, status=404)

            # 기본 정보 수정
            if update_data.job_category is not None:
                resume.job_category = update_data.job_category
            if update_data.resume_title is not None:
                resume.resume_title = update_data.resume_title
            if update_data.education_level is not None:
                resume.education_level = update_data.education_level
            if update_data.school_name is not None:
                resume.school_name = update_data.school_name
            if update_data.education_state is not None:
                resume.education_state = update_data.education_state
            if update_data.introduce is not None:
                resume.introduce = update_data.introduce
            resume.save()

            # 경력 수정
            if update_data.career_list is not None:
                resume.careers.all().delete()
                for career in update_data.career_list:
                    CareerInfo.objects.create(
                        resume=resume,
                        company_name=career.company_name,
                        position=career.position,
                        employment_period_start=career.employment_period_start,
                        employment_period_end=career.employment_period_end,  # type: ignore
                    )

            # 자격증 수정
            if update_data.certification_list is not None:
                resume.certifications.all().delete()
                for certification in update_data.certification_list:
                    Certification.objects.create(
                        resume=resume,
                        certification_name=certification.certification_name,
                        issuing_organization=certification.issuing_organization,
                        date_acquired=certification.date_acquired,
                    )

            career_models = serialize_careers(list(resume.careers.all()))
            certification_models = serialize_certifications(
                list(resume.certifications.all())
            )

            resume_model = ResumeModel(
                resume_id=resume.resume_id,
                job_category=resume.job_category,
                resume_title=resume.resume_title,
                education_level=resume.education_level,
                school_name=resume.school_name,
                education_state=resume.education_state,
                introduce=resume.introduce,
                career_list=career_models,
                certification_list=certification_models,
            )
            response = ResumeResponseModel(
                message="Resume updated successfully", resume=resume_model
            )
            return JsonResponse(response.model_dump(), status=200)

        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=400)

    def delete(
        self, request: HttpRequest, resume_id: uuid.UUID
    ) -> JsonResponse:
        """
        이력서 삭제
        """
        try:
            user = request.user
            resume = Resume.objects.get(user_id=user, resume_id=resume_id)  # type: ignore
            resume.delete()
            return JsonResponse(
                {"message": "Successfully deleted resume"}, status=200
            )
        except Resume.DoesNotExist:
            return JsonResponse({"error": "Resume not found"}, status=404)
        except Exception as e:
            return JsonResponse({"errors": str(e)}, status=400)
