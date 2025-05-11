from datetime import date, time
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from utils.schemas import MY_CONFIG


class JobPostingCreateModel(BaseModel):
    """
    공고 등록을 위한 스키마
    """
    model_config = MY_CONFIG
    job_posting_id : UUID
    company_id: UUID
    job_posting_title: str
    address: str
    city: str
    district: str
    town: str
    location: tuple[float, float]  # (경도, 위도)
    work_time_start: time
    work_time_end: time
    posting_type: str
    employment_type: str
    work_experience: str
    job_keyword_main: str
    job_keyword_sub: List[str]
    number_of_positions: int
    education: str
    deadline: date
    time_discussion: bool
    day_discussion: bool
    work_day: List[str]
    salary_type: str
    salary: int
    summary: str
    content: Optional[str]
    is_bookmarked : bool

class JobPostingResponseModel(BaseModel):
    """
    공고 상세 조회를 위한 모델
    """

    model_config = MY_CONFIG
    job_posting_id: UUID
    company_id: UUID
    company_logo: Optional[str]
    company_name: str
    manager_phone_number: str
    manager_name: str
    job_posting_title: str
    address: str
    city: str
    district: str
    town: str
    location: tuple[float, float]  # (경도, 위도)
    work_time_start: time
    work_time_end: time
    posting_type: str
    employment_type: str
    work_experience: str
    job_keyword_main: str
    job_keyword_sub: List[str]
    number_of_positions: int
    education: str
    deadline: date
    time_discussion: bool
    day_discussion: bool
    work_day: List[str]
    salary_type: str
    salary: int
    summary: str
    content: Optional[str]
    is_bookmarked: bool


class JobPostingDetailResponseModel(BaseModel):
    """
    공고 상세 조회 응답 스키마
    """

    model_config = MY_CONFIG
    message: str
    job_posting: JobPostingResponseModel


class JobPostingListModel(BaseModel):
    """
    공고 리스트 항목 스키마
    """

    model_config = MY_CONFIG
    job_posting_id: UUID
    company_id: UUID
    company_name: str
    company_address: str
    job_posting_title: str
    summary: str
    deadline: date
    is_bookmarked: bool


class JobPostingListResponseModel(BaseModel):
    """
    공고 리스트 조회 응답 스키마
    """

    model_config = MY_CONFIG
    message: str
    data: List[JobPostingListModel]


class JobPostingUpdateModel(BaseModel):
    """
    공고 수정 스키마
    """

    model_config = MY_CONFIG
    job_posting_title: Optional[str]
    address: Optional[str]
    city: Optional[str]
    district: Optional[str]
    town: Optional[str]
    location: Optional[tuple[float, float]]
    work_time_start: Optional[time]
    work_time_end: Optional[time]
    posting_type: Optional[str]
    employment_type: Optional[str]
    work_experience: Optional[str]
    job_keyword_main: Optional[str]
    job_keyword_sub: Optional[List[str]]
    number_of_positions: Optional[int]
    education: Optional[str]
    deadline: Optional[date]
    time_discussion: Optional[bool]
    day_discussion: Optional[bool]
    work_day: Optional[List[str]]
    salary_type: Optional[str]
    salary: Optional[int]
    summary: Optional[str]
    content: Optional[str]


class BookmarkResponseModel(BaseModel):
    """
    북마크 등록/삭제 기본 응답 스키마
    """

    message: str


class JobPostingBookmarkListItemModel(BaseModel):
    """
    북마크 목록 항목 스키마
    """

    job_posting_id: UUID
    job_posting_title: str
    company_name: str
    summary: str
    deadline: date


class JobPostingBookmarkListResponseModel(BaseModel):
    """
    북마크 리스트 조회 응답 스키마
    """

    message: str
    data: List[JobPostingBookmarkListItemModel]
