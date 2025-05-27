from datetime import date
from typing import Optional

from pydantic import BaseModel

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
