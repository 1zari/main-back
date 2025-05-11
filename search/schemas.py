from datetime import date
from typing import Dict, List, Optional
from uuid import UUID

from geojson_pydantic import MultiPolygon
from pydantic import BaseModel, RootModel

from utils.schemas import MY_CONFIG


class JobPostingResultModel(BaseModel):
    model_config = MY_CONFIG

    company_name: str
    job_posting_id: UUID
    job_posting_title: str
    city: str
    district: str
    is_bookmarked: bool
    deadline: date
    summary: str
    company_logo: Optional[str]


class JobPostingSearchQueryModel(BaseModel):
    model_config = MY_CONFIG

    city_no: list[str]
    district_no: list[str]
    town_no: list[str]
    work_day: list[str]
    posting_type: list[str]
    employment_type: list[str]
    education: list[str]
    job_keyword_main: list[str]
    job_keyword_sub: list[str]
    search: str
    work_experience: list[str]
    day_discussion: bool


class JobPostingSearchResponseModel(BaseModel):
    model_config = MY_CONFIG

    results: List[JobPostingResultModel]


class TownCategory(BaseModel):
    """
    읍면동 카테고리
    """

    id: str
    name: str


class DistrictCategory(BaseModel):
    """
    시군구 카테고리
    """

    id: str
    name: str
    towns: list[TownCategory] = []


class CityCategory(BaseModel):
    """
    시도 카테고리
    """

    id: str
    name: str
    districts: list[DistrictCategory]


class RegionTreeResponse(RootModel):
    """
    지역 계층 구조 응답 모델
    """

    root: list[CityCategory]


class JobCategory(BaseModel):
    """
    직업 소분류 카테고리
    """

    id: str
    name: str


class JobCategoryBig(BaseModel):
    """
    직업 대분류 카테고리
    """

    id: str
    name: str
    children: list[JobCategory]


class JobTreeResponse(RootModel):
    """
    직업 카테고리 응담 모델
    """

    root: List[JobCategoryBig]


class DistrictModelDTO(BaseModel):
    geometry: str  # WKT 문자열
    city_no: str
    district_no: str
    emd_no: str

    @classmethod
    def from_orm(cls, obj):
        return cls(
            geometry=obj.geometry.wkt,
            city_no=obj.city_no,
            district_no=obj.district_no,
            emd_no=obj.emd_no,
        )
