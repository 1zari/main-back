from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from job_posting.schemas import JobPostingBaseModel, JobPostingListModel
from user.schemas import UserInfoModel
from utils.schemas import CustomBaseModel


# ------------------------
# Career (경력 정보)
# ------------------------


class CareerInfoBaseModel(CustomBaseModel):
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


class CertificationBaseModel(CustomBaseModel):
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


class ResumeBaseModel(CustomBaseModel):
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


class ResumeUpdateModel(CustomBaseModel):
    education: Optional[str] = None
    introduce: Optional[str] = None
    career_list: Optional[List[CareerInfoCreateModel]] = None
    certification_list: Optional[List[CertificationInfoCreateModel]] = None

class ResumeInfoModel(ResumeBaseModel):
    pass

class ResumeModel(ResumeBaseModel):
    resume_id: UUID
    user : UserInfoModel
    career_list: List[CareerInfoModel]
    certification_list: List[CertificationInfoModel]


# ------------------------
# Submission (지원한 이력서)
# ------------------------
class JobpostingListOutputModel(JobPostingListModel):
    model_config = ConfigDict(extra='ignore')

class SubmissionBaseModel(CustomBaseModel):
    job_posting : JobPostingBaseModel
    resume : ResumeModel
    memo : Optional[str] = ""
    is_read : bool

class SubmissionModel(SubmissionBaseModel):
    submission_id : UUID
    job_posting : JobpostingListOutputModel
    created_at: date




# ------------------------
# 응답 모델
# ------------------------


class ResumeResponseModel(CustomBaseModel):
    message: str
    resume: ResumeModel


class ResumeListResponseModel(CustomBaseModel):
    message: str
    resume_list: List[ResumeModel]

class SubmissionListResponseModel(CustomBaseModel):
    message : str
    submission_list : List[SubmissionModel]

