from django.urls.conf import path

from user.views.views import (
    CompanyLoginView,
    CompanySignupView,
    TokenRefreshView,
    UserLoginView,
    UserSignupView,
)

app_name = "user"


urlpatterns = [
    path("user/signup/", UserSignupView.as_view(), name="user_signup"),
    path("company/signup/", CompanySignupView.as_view(), name="company_signup"),
    path("user/login/", UserLoginView.as_view(), name="user_login"),
    path("company/login/", CompanyLoginView.as_view(), name="company_login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
