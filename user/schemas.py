from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from utils.schemas import MY_CONFIG

# ------------------------
# 공통 유저 (CommonUser)
# ------------------------


class CommonUserBaseModel(BaseModel):
    model_config = MY_CONFIG

    email: EmailStr
    join_type: str
    password: str


class CommonUserResponseModel(BaseModel):
    model_config = MY_CONFIG

    common_user_id: UUID
    email: EmailStr
    join_type: str
    last_login: Optional[str] = None
    is_active: bool = False
    is_staff: bool = False


# ------------------------
# 일반 유저 가입 요청 모델
# ------------------------


class UserSignupRequest(BaseModel):
    model_config = MY_CONFIG

    common_user_id: UUID
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
    model_config = MY_CONFIG

    name: str
    phone_number: str
    gender: str
    birthday: Optional[date] = None
    interest: List[str] = Field(default_factory=list)
    purpose_subscription: List[str] = Field(default_factory=list)
    route: List[str] = Field(default_factory=list)


class UserInfoModel(BaseModel):
    model_config = MY_CONFIG

    user_id: UUID
    name: str
    phone_number: str
    gender: str
    birthday: Optional[date] = None
    interest: List[str] = Field(default_factory=list)
    purpose_subscription: List[str] = Field(default_factory=list)
    route: List[str] = Field(default_factory=list)


# ------------------------
# 기업 유저 가입 요청 모델
# ------------------------


class CompanySignupRequest(BaseModel):
    model_config = MY_CONFIG

    common_user_id: UUID
    company_name: str
    establishment: date
    company_address: str
    business_registration_number: str
    company_introduction: str
    ceo_name: str
    manager_name: str
    manager_phone_number: str
    manager_email: EmailStr

# ------------------------
# 기업 유저 (CompanyInfo)
# ------------------------


class CompanyInfoBaseModel(BaseModel):
    model_config = MY_CONFIG

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


class CompanyInfoModel(BaseModel):
    model_config = MY_CONFIG

    company_id: UUID
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


# ------------------------
# 응답 모델
# ------------------------


class UserJoinResponseModel(BaseModel):
    model_config = MY_CONFIG

    message: str
    common_user: CommonUserResponseModel
    user_info: Optional[UserInfoModel] = None


class CompanyJoinResponseModel(BaseModel):
    model_config = MY_CONFIG

    message: str
    common_user: CommonUserResponseModel
    company_info: Optional[CompanyInfoModel] = None


# ------------------------
# 로그인 요청 모델
# ------------------------


class UserLoginRequest(BaseModel):
    model_config = MY_CONFIG

    email: EmailStr
    password: str


class CompanyLoginRequest(BaseModel):
    model_config = MY_CONFIG

    email: EmailStr
    password: str


# ------------------------
# 로그인 응답 모델
# ------------------------


class UserLoginResponse(BaseModel):
    model_config = MY_CONFIG

    message: str
    access_token: str
    refresh_token: str
    token_type: str


class CompanyLoginResponse(BaseModel):
    model_config = MY_CONFIG

    message: str
    access_token: str
    refresh_token: str
    token_type: str

# ------------------------
# 회원정보 조회 응답 모델
# ------------------------
class UserInfoResponse(BaseModel):
    model_config = MY_CONFIG

    message: str
    name: Optional[str]
    phone_number: Optional[str]
    gender: Optional[str]
    birthday: Optional[date]
    interest: Optional[List[str]]
    purpose_subscription: Optional[List[str]]
    route: Optional[List[str]]

class CompanyInfoResponse(BaseModel):
    model_config = MY_CONFIG

    message: str
    company_id: UUID
    common_user_id: UUID
    company_name: str
    establishment: Optional[date]
    company_address: Optional[str]
    business_registration_number: Optional[str]
    company_introduction: Optional[str]
    ceo_name: Optional[str]
    manager_name: Optional[str]
    manager_phone_number: Optional[str]
    manager_email: Optional[EmailStr]
    certificate_image: Optional[str]
    company_logo: Optional[str]


# ------------------------
# 회원정보 수정 요청 모델
# ------------------------


class UserInfoUpdateRequest(BaseModel):
    model_config = MY_CONFIG

    name: Optional[str] = None
    phone_number: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[date] = None
    interest: Optional[List[str]] = None
    purpose_subscription: Optional[List[str]] = None
    route: Optional[List[str]] = None


class CompanyInfoUpdateRequest(BaseModel):
    company_name: Optional[str] = None
    establishment: Optional[date] = None
    company_address: Optional[str] = None
    business_registration_number: Optional[str] = None
    company_introduction: Optional[str] = None
    ceo_name: Optional[str] = None
    manager_name: Optional[str] = None
    manager_phone_number: Optional[str] = None
    manager_email: Optional[str] = None


# ------------------------
# 회원정보 수정 응답 모델
# ------------------------


class UserInfoUpdateResponse(BaseModel):
    model_config = MY_CONFIG

    message: str
    name: Optional[str] = None
    phone_number: Optional[str] = None
    gender: Optional[str] = None
    birthday: Optional[date] = None
    interest: Optional[List[str]] = None
    purpose_subscription: Optional[List[str]] = None
    route: Optional[List[str]] = None


class CompanyInfoUpdateResponse(BaseModel):
    model_config = MY_CONFIG

    message: str
    company_name: Optional[str] = None
    establishment: Optional[date] = None
    company_address: Optional[str] = None
    business_registration_number: Optional[str] = None
    company_introduction: Optional[str] = None
    ceo_name: Optional[str] = None
    manager_name: Optional[str] = None
    manager_phone_number: Optional[str] = None
    manager_email: Optional[str] = None


# ------------------------
# 로그아웃 요청 모델
# ------------------------


class LogoutRequest(BaseModel):
    model_config = MY_CONFIG

    refresh_token: str


# ------------------------
# 로그아웃 응답 모델
# ------------------------


class LogoutResponse(BaseModel):
    model_config = MY_CONFIG

    message: str


# ------------------------
# 토큰 갱신 모델
# ------------------------


class TokenRefreshRequest(BaseModel):
    model_config = MY_CONFIG

    refresh_token: str


class TokenRefreshResponse(BaseModel):
    model_config = MY_CONFIG

    access_token: str
    token_type: str


# ------------------------
# 토큰 검증 모델
# ------------------------


class TokenVerificationResponse(BaseModel):
    model_config = MY_CONFIG

    valid: bool
    message: str


# ------------------------
# 문자 인증 모델
# ------------------------


class SendVerificationCodeRequest(BaseModel):
    model_config = MY_CONFIG

    phone_number: str


class VerifyCodeRequest(BaseModel):
    model_config = MY_CONFIG

    phone_number: str
    code: str


# ------------------------
# 사업자등록번호 검증 모델
# ------------------------


class VerifyBusinessRegistrationRequest(BaseModel):
    model_config = MY_CONFIG

    b_no: str  # 사업자등록번호
    p_nm: str  # 대표자 이름
    start_dt: str  # 개업일자


# ------------------------
# oauth 요청 모델
# ------------------------


class KakaoLoginRequest(BaseModel):
    model_config = MY_CONFIG

    code: str


class NaverLoginRequest(BaseModel):
    model_config = MY_CONFIG

    code: str
    state: str


# ------------------------
# oauth 응답 모델
# ------------------------


class KakaoLoginResponse(BaseModel):
    model_config = MY_CONFIG

    message: str
    access_token: str
    refresh_token: str
    token_type: str


class NaverLoginResponse(BaseModel):
    model_config = MY_CONFIG

    message: str
    access_token: str
    refresh_token: str
    token_type: str


# ------------------------
# 이메일, 비밀번호 찾기 요청 모델
# ------------------------


class FindUserEmailRequest(BaseModel):
    model_config = MY_CONFIG

    phone_number: str


class ResetUserPasswordRequest(BaseModel):
    model_config = MY_CONFIG

    email: EmailStr
    phone_number: str
    new_password: str


class FindCompanyEmailRequest(BaseModel):
    model_config = MY_CONFIG

    phone_number: str
    business_registration_number: str


class ResetCompanyPasswordRequest(BaseModel):
    model_config = MY_CONFIG

    email: EmailStr
    phone_number: str
    business_registration_number: str
    new_password: str


# ------------------------
# 이메일, 비밀번호 찾기 응답 모델
# ------------------------


class FindUserEmailResponse(BaseModel):
    model_config = MY_CONFIG

    email: str
    message: Optional[str] = None  # 성공 메시지
    errors: Optional[List[str]] = None  # 오류 메시지


class ResetUserPasswordResponse(BaseModel):
    model_config = MY_CONFIG

    message: str
    errors: Optional[List[str]] = None


class FindCompanyEmailResponse(BaseModel):
    model_config = MY_CONFIG

    email: str
    message: Optional[str] = None
    errors: Optional[List[str]] = None


class ResetCompanyPasswordResponse(BaseModel):
    model_config = MY_CONFIG

    message: str
    errors: Optional[List[str]] = None
