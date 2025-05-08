from typing import Union

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied

from user.models import CommonUser, CompanyInfo, UserInfo


def get_valid_normal_user(token: Union[CommonUser, AnonymousUser]) -> UserInfo:
    if not token.is_authenticated:
        raise PermissionDenied("Authentication is required.")
    if token.join_type != "normal":
        raise PermissionDenied("Only 'normal' users are allowed.")
    user = UserInfo.objects.filter(common_user=token.common_user_id).first()
    if user is None:
        raise PermissionDenied("UserInfo does not exist.")
    return user


def get_valid_company_user(
    token: Union[CommonUser, AnonymousUser],
) -> CompanyInfo:
    if not token.is_authenticated:
        raise PermissionDenied("Authentication is required.")
    if token.join_type != "company":
        raise PermissionDenied("Only 'company' users are allowed.")
    user = CompanyInfo.objects.filter(common_user=token.common_user_id).first()
    if user is None:
        raise PermissionDenied("CompanyInfo does not exist.")
    return user
