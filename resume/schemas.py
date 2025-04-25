from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from job_posting.schemas import JobPostingListModel
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
    user: UserInfoModel
    career_list: Optional[List[CareerInfoModel]]
    certification_list: Optional[List[CertificationInfoModel]]

class SubmissionOutputModel(BaseModel):
    model_config = MY_CONFIG
    job_category: str = ""
    resume_title: str
    education_level: str
    school_name: str
    education_state: str
    introduce: str
    career_list: Optional[List[CareerInfoModel]]
    certification_list: Optional[List[CertificationInfoModel]]
# ------------------------
# Submission (지원한 이력서)
# ------------------------
class JobpostingListOutputModel(BaseModel):
    """
    채용공고 내보내기 모델
    """
    model_config = MY_CONFIG
    job_posting_id: UUID
    city : str
    district : str
    company_name: str
    company_address: str
    job_posting_title: str
    summary: str
    deadline: date
    is_bookmarked: bool


class SnapshotResumeModel(BaseModel):
    model_config = MY_CONFIG

    job_category: str
    resume_title: str
    education_level: str
    school_name: str
    education_state: str
    introduce: str
    career_list: list[CareerInfoModel]
    certification_list: list[CertificationInfoModel]


class SubmissionModel(BaseModel):
    """
    공고 지원서 모델
    """

    model_config = MY_CONFIG

    submission_id: UUID
    job_posting: JobpostingListOutputModel
    snapshot_resume: SnapshotResumeModel
    memo: Optional[str] = None
    is_read: bool
    created_at: date


class SubmissionMemoUpdateModel(BaseModel):
    memo: Optional[str] = None


class JobpostingGetListModel(BaseModel):
    """
    기업 유저 지원자 목록 조회 시 드롭다운 항목
    """

    model_config = MY_CONFIG

    job_posting_id: UUID
    job_posting_title: str


class SubmissionGetListModel(BaseModel):
    """
    내 지원 목록 보여질 때 지원 정보
    """

    model_config = MY_CONFIG

    company_name: str
    company_address: str
    summary: str
    deadline: date
    is_bookmarked: bool
    resume_title: str
    memo: Optional[str] = None
    created_at: date


class SubmissionGetListInfoModel(BaseModel):
    model_config = MY_CONFIG


class SubmissionCompanyGetListInfoModel(BaseModel):
    """
    기업 유저 지원자 목록 조회 포함 항목
    """

    model_config = MY_CONFIG

    submission_id: UUID
    job_posting_id :UUID
    user_name: str
    summary: str
    is_read: bool
    created_at: date
    resume_title: str


class SubmissionCompanyGetListOutputModel(BaseModel):
    """
    기업 유저 지원자 목록 조회 시 보여질 모든 항목
    """

    model_config = MY_CONFIG

    message: str
    job_posting_list: list[JobpostingGetListModel]
    submission_list: list[SubmissionCompanyGetListInfoModel]


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

class SubmissionMemoResponseModel(BaseModel):
    message : str
    memo : Optional[str] = None
