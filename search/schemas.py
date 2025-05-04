from datetime import date
from typing import Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, RootModel

from utils.schemas import MY_CONFIG


class JobPostingResultModel(BaseModel):
    model_config = MY_CONFIG

    job_posting_id: UUID
    job_posting_title: str
    city: str
    district: str
    is_bookmarked: bool
    deadline: date


class JobPostingSearchQueryModel(BaseModel):
    model_config = MY_CONFIG

    city: list[str]
    district: list[str]
    town: list[str]
    work_day: list[str]
    posting_type: list[str]
    employment_type: list[str]
    education: str
    search: str


class JobPostingSearchResponseModel(BaseModel):
    model_config = MY_CONFIG

    results: List[JobPostingResultModel]


class RegionTreeResponse(RootModel[Dict[str, Dict[str, List[str]]]]):
    """
    지역 계층 구조 응답 모델
    """


class JonTreeResponse(RootModel[Dict[str, list[str]]]):
    """
    직업 카테고리 응담 모델
    """
