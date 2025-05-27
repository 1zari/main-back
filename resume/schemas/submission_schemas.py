from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from resume.schemas.common_schemas import CareerInfoModel, CertificationInfoModel
from utils.schemas import MY_CONFIG


# ------------------------
# Submission (지원한 이력서)
# ------------------------
class JobpostingListOutputModel(BaseModel):
    """
    채용공고 리스트 내보내기 모델
    """

    model_config = MY_CONFIG
    job_posting_id: UUID
    city: str
    district: str
    town: str
    company_name: str
    company_address: str
    job_posting_title: str
    summary: str
    deadline: date
    is_bookmarked: bool


class SnapshotResumeModel(BaseModel):
    """
    이력서 스냅샷 모델
    """
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
    """
    메모 모델
    """
    memo: Optional[str] = None

class JobpostingGetListModel(BaseModel):
    """
    기업 유저 지원자 목록 조회 시 드롭다운 항목
    """

    model_config = MY_CONFIG

    job_posting_id: UUID
    job_posting_title: str

class SubmissionCompanyOutputDetailModel(BaseModel):
    model_config = MY_CONFIG

    job_category: str
    name: str
    phone_number: str
    email: str
    resume_title: str
    education_level: str
    school_name: str
    education_state: str
    introduce: str
    career_list: list[CareerInfoModel]
    certification_list: list[CertificationInfoModel]

class SubmissionCompanyGetListInfoModel(BaseModel):
    """
    기업 유저 지원자 목록 조회 포함 항목
    """

    model_config = MY_CONFIG

    submission_id: UUID
    job_posting_id: UUID
    name: str
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

class SubmissionListResponseModel(BaseModel):
    message: str
    submission_list: List[SubmissionModel]


class SubmissionDetailResponseModel(BaseModel):
    message: str
    submission: SubmissionModel


class SubmissionMemoResponseModel(BaseModel):
    message: str
    memo: Optional[str] = None


class SubmissionCompanyDetailModel(BaseModel):
    message: str
    submission: SubmissionCompanyOutputDetailModel
