from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ------------------------
# Career (경력 정보)
# ------------------------


class CareerInfoBaseModel(BaseModel):
    company_name: str
    position: str
    employment_period_start: date
    employment_period_end: Optional[date] = None

    class Config:
        json_encoders = {date: lambda v: v.strftime("%Y-%m-%d")}


class CareerInfoCreateModel(CareerInfoBaseModel):
    pass


class CareerInfoModel(CareerInfoBaseModel):
    pass


# ------------------------
# Certification (자격증)
# ------------------------


class CertificationBaseModel(BaseModel):
    certification_name: str
    issuing_organization: str
    date_acquired: date


class CertificationInfoCreateModel(CertificationBaseModel):
    pass


class CertificationInfoModel(CertificationBaseModel):
    pass


# ------------------------
# Resume (이력서)
# ------------------------


class ResumeBaseModel(BaseModel):
    job_category: str = ""
    resume_title: str
    education_level: str
    school_name: str
    education_state: str
    introduce: str

    career_list: List[CareerInfoCreateModel] = Field(default_factory=list)
    certification_list: List[CertificationInfoCreateModel] = Field(
        default_factory=list
    )


class ResumeCreateModel(ResumeBaseModel):
    pass


class ResumeUpdateModel(BaseModel):
    job_category: str = ""
    resume_title: str
    education_level: str
    school_name: str
    education_state : str
    introduce: str
    career_list: Optional[List[CareerInfoCreateModel]] = None
    certification_list: Optional[List[CertificationInfoCreateModel]] = None


class ResumeModel(BaseModel):
    model_config = ConfigDict()
    resume_id: UUID
    job_category: str = ""
    resume_title: str
    education_level: str
    school_name: str
    education_state: str
    introduce: str
    career_list: List[CareerInfoModel]
    certification_list: List[CertificationInfoModel]


# ------------------------
# Submission (지원한 이력서)
# ------------------------


# ------------------------
# 응답 모델
# ------------------------


class ResumeResponseModel(BaseModel):
    message: str
    resume: ResumeModel


class ResumeListResponseModel(BaseModel):
    message: str
    resume_list: List[ResumeModel]
