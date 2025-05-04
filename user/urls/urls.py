from django.urls.conf import path

from user.views.views import (
    CommonUserCreateView,
    EmailDuplicateCheckView,
    LogoutView,
    UserDeleteView,
    UserFindEmailView,
    UserInfoDetailView,
    UserInfoUpdateView,
    UserLoginView,
    UserResetPasswordView,
    UserSignupView,
)
from user.views.views_company import (
    CompanyFindEmailView,
    CompanyInfoDetailView,
    CompanyInfoUpdateView,
    CompanyLoginView,
    CompanyResetPasswordView,
    CompanySignupView,
)
from user.views.views_oauth import KakaoLoginView, NaverLoginView
from user.views.views_token import TokenRefreshView
from user.views.views_verify import (
    SendVerificationCodeView,
    VerifyBusinessRegistrationView,
    VerifyCodeView,
)

app_name = "user"


urlpatterns = [
    # 공통 유저 (common)
    path(
        "common/signup/", CommonUserCreateView.as_view(), name="common-signup"
    ),
    path(
        "email/check/",
        EmailDuplicateCheckView.as_view(),
        name="email-duplicate-check",
    ),
    # 일반 유저 (normal)
    path("normal/signup/", UserSignupView.as_view(), name="normal-signup"),
    path("normal/login/", UserLoginView.as_view(), name="normal-login"),
    path(
        "normal/info/", UserInfoDetailView.as_view(), name="normal-info-detail"
    ),
    path(
        "normal/info/update/",
        UserInfoUpdateView.as_view(),
        name="normal-info-update",
    ),
    path(
        "normal/find/email/",
        UserFindEmailView.as_view(),
        name="normal-find-email",
    ),
    path(
        "normal/reset/password/",
        UserResetPasswordView.as_view(),
        name="normal-reset-password",
    ),
    # 기업 유저 (company)
    path("company/signup/", CompanySignupView.as_view(), name="company-signup"),
    path("company/login/", CompanyLoginView.as_view(), name="company-login"),
    path(
        "company/info/",
        CompanyInfoDetailView.as_view(),
        name="company-info-detail",
    ),
    path(
        "company/info/update/",
        CompanyInfoUpdateView.as_view(),
        name="company-info-update",
    ),
    path(
        "company/find/email/",
        CompanyFindEmailView.as_view(),
        name="company-find-email",
    ),
    path(
        "company/reset/password/",
        CompanyResetPasswordView.as_view(),
        name="company-reset-password",
    ),
    # 인증 관련 (verify)
    path(
        "verify/send-code/",
        SendVerificationCodeView.as_view(),
        name="send-verification-code",
    ),
    path("verify/code/", VerifyCodeView.as_view(), name="verify-code"),
    path(
        "verify/business/",
        VerifyBusinessRegistrationView.as_view(),
        name="verify-business",
    ),
    # OAuth 로그인
    path("oauth/kakao/login/", KakaoLoginView.as_view(), name="kakao-login"),
    path("oauth/naver/login/", NaverLoginView.as_view(), name="naver-login"),
    # 토큰 관련
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("delete/", UserDeleteView.as_view(), name="user-delete"),
]
