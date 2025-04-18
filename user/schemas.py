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


class CommonUserModel(CommonUserBaseModel):
    common_user_id: UUID


# ------------------------
# 일반 유저 가입 요청 모델
# ------------------------


class UserSignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone_number: str
    gender: str
    birthday: Optional[date] = None
    interest: List[str] = Field(default_factory=list)
    purpose_subscription: List[str] = Field(default_factory=list)
    route: List[str] = Field(default_factory=list)

    class Config:
        orm_mode = True


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


class UserInfoModel(UserInfoBaseModel):
    user_id: UUID


# ------------------------
# 기업 유저 가입 요청 모델
# ------------------------


class CompanySignupRequest(BaseModel):
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

    class Config:
        orm_mode = True


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


class CompanyInfoModel(CompanyInfoBaseModel):
    company_id: UUID


# ------------------------
# 응답 모델
# ------------------------


class UserJoinResponseModel(BaseModel):
    message: str
    common_user: CommonUserModel
    user_info: Optional[UserInfoModel] = None

    class Config:
        orm_mode = True


class CompanyJoinResponseModel(BaseModel):
    message: str
    common_user: CommonUserModel
    company_info: Optional[CompanyInfoModel] = None

    class Config:
        orm_mode = True


# ------------------------
# 로그인 모델
# ------------------------


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class CompanyLoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserLoginResponse(BaseModel):
    message: str
    access_token: str
    refresh_token: str
    token_type: str


class CompanyLoginResponse(BaseModel):
    message: str
    access_token: str
    refresh_token: str
    token_type: str


# ------------------------
# 로그아웃 요청 모델
# ------------------------


class LogoutRequest(BaseModel):
    refresh_token: str


# ------------------------
# 토큰 갱신 모델
# ------------------------


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str


# ------------------------
# 토큰 검증 모델
# ------------------------


class TokenVerificationResponse(BaseModel):
    valid: bool
    message: str


# ------------------------
# 문자 인증 모델
# ------------------------


class SendVerificationCodeRequest(BaseModel):
    phone_number: str


class VerifyCodeRequest(BaseModel):
    phone_number: str
    code: str


# ------------------------
# 사업자등록번호 검증 모델
# ------------------------


class VerifyBusinessRegistrationRequest(BaseModel):
    b_no: str  # 사업자등록번호
    p_nm: str  # 대표자 이름
    start_dt: str  # 개업일자
