from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from job_posting.schemas import JobPostingBaseModel, JobPostingListModel
from user.models import UserInfo
from user.schemas import UserInfoModel
from utils.schemas import MY_CONFIG

# ------------------------
# Career (경력 정보)
# ------------------------


class CareerInfoModel(BaseModel):
    model_config = MY_CONFIG

    company_name: str
    position: str
    employment_period_start: date
    employment_period_end: Optional[date] = None


# ------------------------
# Certification (자격증)
# ------------------------


class CertificationInfoModel(BaseModel):
    model_config = MY_CONFIG

    certification_name: str
    issuing_organization: str
    date_acquired: date


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
    user: UserInfo
    career_list: Optional[List[CareerInfoModel]]
    certification_list: Optional[List[CertificationInfoModel]]


# ------------------------
# Submission (지원한 이력서)
# ------------------------
class JobpostingListOutputModel(JobPostingListModel):
    """
    채용공고 내보내기 모델
    """

    model_config = MY_CONFIG


class SubmissionModel(BaseModel):
    """
    공고 지원서 모델
    """

    model_config = MY_CONFIG

    submission_id: UUID
    job_posting: JobpostingListOutputModel
    snapshot_resume: ResumeOutputModel
    memo: str = ""
    is_read: bool
    created_at: date


class SubmissionMemoUpdateModel(BaseModel):
    memo: str = ""


# ------------------------
# 응답 모델
# ------------------------


class ResumeResponseModel(BaseModel):
    message: str
    resume: ResumeOutputModel


class ResumeListResponseModel(BaseModel):
    message: str
    resume_list: List[ResumeOutputModel]


class SubmissionListResponseModel(BaseModel):
    message: str
    submission_list: List[SubmissionModel]


class SubmissionDetailResponseModel(BaseModel):
    message: str
    submission: SubmissionModel
