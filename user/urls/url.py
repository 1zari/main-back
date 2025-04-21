from django.urls.conf import path

from user.views.views import (
    CommonUserCreateView,
    CompanyLoginView,
    CompanySignupView,
    KakaoLoginView,
    LogoutView,
    NaverLoginView,
    UserLoginView,
    UserSignupView,
)
from user.views.views_token import TokenRefreshView
from user.views.views_verify import (
    SendVerificationCodeView,
    VerifyBusinessRegistrationView,
    VerifyCodeView,
)

app_name = "user"


urlpatterns = [
    path(
        "common_user/signup/",
        CommonUserCreateView.as_view(),
        name="common_signup",
    ),
    path("signup/", UserSignupView.as_view(), name="user-signup"),
    path("login/", UserLoginView.as_view(), name="user-login"),
    path("company/signup/", CompanySignupView.as_view(), name="company-signup"),
    path("company/login/", CompanyLoginView.as_view(), name="company-login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
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
    path("kakao/login/", KakaoLoginView.as_view(), name="kakao-login"),
    path("naver/login/", NaverLoginView.as_view(), name="naver-login"),
]
