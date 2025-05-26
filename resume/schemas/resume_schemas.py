from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from resume.schemas.common_schemas import CareerInfoModel, CertificationInfoModel
from user.schemas import UserInfoModel
from utils.schemas import MY_CONFIG

# ------------------------
# Resume (이력서)
# ------------------------


class ResumeCreateModel(BaseModel):
    """
    이력서 생성 model
    """

    model_config = MY_CONFIG
    job_category: str = ""
    resume_title: str
    education_level: str
    school_name: str
    education_state: str
    introduce: str

    career_list: Optional[List[CareerInfoModel]] = None
    certification_list: Optional[List[CertificationInfoModel]] = None


class ResumeUpdateModel(BaseModel):
    """
    이력서 수정 model
    """

    resume_id: UUID
    job_category: Optional[str] = None
    resume_title: Optional[str] = None
    education_level: Optional[str] = None
    school_name: Optional[str] = None
    education_state: Optional[str] = None
    introduce: Optional[str] = None
    career_list: Optional[List[CareerInfoModel]] = None
    certification_list: Optional[List[CertificationInfoModel]] = None


class ResumeListOutputModel(BaseModel):
    """
    이력서 리스트 조회
    """

    model_config = MY_CONFIG
    resume_id: UUID
    resume_title: str
    job_category: str
    updated_at: date


class ResumeOutputModel(BaseModel):
    """
    이력서
    """

    model_config = MY_CONFIG
    resume_id: UUID
    job_category: str = ""
    resume_title: str
    education_level: str
    school_name: str
    education_state: str
    introduce: str
    user: UserInfoModel
    career_list: Optional[List[CareerInfoModel]]
    certification_list: Optional[List[CertificationInfoModel]]


class ResumeResponseModel(BaseModel):
    message: str
    resume: ResumeOutputModel


class MyResume(BaseModel):
    """
    이력서 상세보기 시 id, title
    """

    model_config = MY_CONFIG
    resume_id: UUID
    resume_title: str


# ------------------------
# Resume 응답 모델
# ------------------------


class MyResumeListOutput(BaseModel):
    """
    이력서 상세보기 시 id, title 리스트
    """

    model_config = MY_CONFIG
    resume_id: UUID
    job_category: str = ""
    resume_title: str
    education_level: str
    school_name: str
    education_state: str
    introduce: str
    user: UserInfoModel
    career_list: Optional[List[CareerInfoModel]]
    certification_list: Optional[List[CertificationInfoModel]]
    resume_list: list[MyResume]


class MyResumeMixinResponse(BaseModel):
    """
    resume 상세 조회 시 유저의 resume 목록(id, title)포함 모델
    """

    message: str
    resume: MyResumeListOutput


class ResumeListResponseModel(BaseModel):
    message: str
    resume_list: List[ResumeListOutputModel]
