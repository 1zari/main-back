import jwt
from django.conf import settings
from django.core.exceptions import PermissionDenied

from user.models import CommonUser, CompanyInfo, UserInfo


def get_user_from_token(request):
    auth_header = request.META.get("HTTP_AUTHORIZATION", "")
    if not auth_header.startswith("Bearer "):
        return None  # 또는 인증 실패 처리

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        user_id = payload.get("sub")  # 또는 'user_id', 'username' 등
        if not user_id:
            raise PermissionDenied("Token payload missing user id.")

        # DB에서 유저 존재 확인
        user = CommonUser.objects.filter(pk=user_id).first()
        if not user:
            raise PermissionDenied("User does not exist.")

        return user

    except jwt.ExpiredSignatureError:
        raise PermissionDenied("Token is expired")
    except jwt.InvalidTokenError:
        raise PermissionDenied("Invalid token")


def check_and_return_normal_user(valid_user: CommonUser) -> UserInfo:
    if valid_user.join_type != "normal":
        raise PermissionDenied("Only 'normal' users are allowed.")
    user = UserInfo.objects.select_related("common_user").filter(common_user=valid_user).first()
    if user is None:
        raise PermissionDenied("UserInfo does not exist.")
    return user


def check_and_return_company_user(valid_user: CommonUser) -> CompanyInfo:
    if valid_user.join_type != "company":
        raise PermissionDenied("Only 'company' users are allowed.")
    user = CompanyInfo.objects.select_related("common_user").filter(common_user=valid_user).first()
    if user is None:
        raise PermissionDenied("UserInfo does not exist.")
    return user
