from django.urls.conf import path

from user.views.views import UserSignupView, CompanySignupView

app_name = "user"


urlpatterns = [
    path('user/signup/', UserSignupView.as_view(), name='user_signup'),
    path('company/signup/', CompanySignupView.as_view(), name='company_signup'),
]
