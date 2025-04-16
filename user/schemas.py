from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

# ------------------------
# 공통 유저 (CommonUser)
# ------------------------


class CommonUserBaseModel(BaseModel):
    email: EmailStr
    join_type: str
    password: str

    class Config:
        orm_mode = True


class CommonUserCreateModel(CommonUserBaseModel):
    pass


class CommonUserModel(CommonUserBaseModel):
    common_user_id: UUID


# ------------------------
# 일반 유저 가입 요청 모델
# ------------------------


class PersonalUserSignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone_number: str
    gender: str
    birthday: Optional[date] = None
    interest: List[str] = Field(default_factory=list)
    purpose_subscription: List[str] = Field(default_factory=list)
    route: List[str] = Field(default_factory=list)


# ------------------------
# 일반 유저 (UserInfo)
# ------------------------


class UserInfoBaseModel(BaseModel):
    name: str
    phone_number: str
    gender: str
    birthday: Optional[date] = None
    interest: List[str] = Field(default_factory=list)
    purpose_subscription: List[str] = Field(default_factory=list)
    route: List[str] = Field(default_factory=list)

    class Config:
        orm_mode = True


class UserInfoCreateModel(UserInfoBaseModel):
    pass


class UserInfoModel(UserInfoBaseModel):
    user_id: UUID


# ------------------------
# 기업 유저 가입 요청 모델
# ------------------------


class CompanyUserSignupRequest(BaseModel):
    email: EmailStr
    password: str
    company_name: str
    establishment: date
    company_address: str
    business_registration_number: str
    company_introduction: str
    certificate_image: str
    company_logo: Optional[str] = None
    ceo_name: str
    manager_name: str
    manager_phone_number: str
    manager_email: EmailStr
    is_staff: bool


# ------------------------
# 기업 유저 (CompanyInfo)
# ------------------------


class CompanyInfoBaseModel(BaseModel):
    company_name: str
    establishment: date
    company_address: str
    business_registration_number: str
    company_introduction: str
    certificate_image: str
    company_logo: Optional[str] = None
    ceo_name: str
    manager_name: str
    manager_phone_number: str
    manager_email: EmailStr
    is_staff: bool

    class Config:
        orm_mode = True


class CompanyInfoCreateModel(CompanyInfoBaseModel):
    pass


class CompanyInfoModel(CompanyInfoBaseModel):
    company_id: UUID


# ------------------------
# 응답 모델
# ------------------------


class UserJoinResponseModel(BaseModel):
    message: str
    common_user: CommonUserModel
    user_info: Optional[UserInfoModel] = None


class CompanyJoinResponseModel(BaseModel):
    message: str
    common_user: CommonUserModel
    company_info: Optional[CompanyInfoModel] = None
