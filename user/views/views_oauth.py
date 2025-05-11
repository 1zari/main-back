from typing import Any, Optional
import json

import requests
from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views import View

from user.models import CommonUser
from user.schemas import (
    KakaoLoginResponse,
    NaverLoginResponse,
)
from user.services.token import create_access_token, create_refresh_token


def create_dummy_password(common_user: CommonUser) -> None:
    dummy_password = CommonUser.objects.make_random_password()
    common_user.set_password(dummy_password)
    common_user.save()
    return dummy_password


class KakaoLoginView(View):

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        try:
            body = json.loads(request.body)
            access_token = body.get("access_token")
            if not access_token:
                return JsonResponse({"message": "Access token is required."}, status=400)

            user_data = self.get_kakao_user_info(access_token)
            if not user_data:
                return JsonResponse({"message": "Failed to retrieve Kakao user info."}, status=400)

            email = user_data.get("kakao_account", {}).get("email")
            common_user = self.get_or_create_common_user(email)

            if common_user:
                if hasattr(common_user, "userinfo"):
                    common_user.last_login = timezone.now()
                    common_user.save()
                    access_token_jwt = create_access_token(common_user)
                    refresh_token = create_refresh_token(common_user)
                    response = KakaoLoginResponse(
                        message="Login successful.",
                        access_token=access_token_jwt,
                        refresh_token=refresh_token,
                        token_type="bearer",
                        common_user_id=common_user.common_user_id,
                        email=common_user.email,
                        name=common_user.userinfo.name,
                        join_type=common_user.join_type,
                        )
                    return JsonResponse(response.model_dump(), status=200)

                return JsonResponse(
                    {
                        "message": "Additional information required.",
                        "email": email,
                    },
                    status=202,
                )

            return JsonResponse({"message": "Failed to create user."}, status=400)

        except Exception as e:
            return JsonResponse({"message": "Server error", "error": str(e)}, status=500)

    def get_kakao_user_info(self, kakao_access_token: str) -> Optional[dict[str, Any]]:
        """카카오 액세스 토큰으로 사용자 정보를 가져오는 메서드"""
        url = settings.KAKAO_USER_INFO_URL
        headers = {"Authorization": f"Bearer {kakao_access_token}"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            return None

    def get_or_create_common_user(self, email: str) -> Optional[CommonUser]:
        """이메일로 기존 사용자 조회 및 없다면 생성하는 메서드"""
        common_user = CommonUser.objects.filter(email=email).first()
        if not common_user:
            # 커먼유저가 존재하지 않으면 새로 생성하고 더미 비밀번호 추가
            common_user = CommonUser.objects.create(
                email=email,
                join_type="normal",
                is_active=True,
            )
            create_dummy_password(common_user)  # 더미 비밀번호 생성
        return common_user


class NaverLoginView(View):
    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> JsonResponse:
        try:
            body = json.loads(request.body)
            access_token = body.get("access_token")
            if not access_token:
                return JsonResponse({"message": "Access token is required."}, status=400)

            user_data = self.get_naver_user_info(access_token)
            if not user_data:
                return JsonResponse({"message": "Failed to retrieve Naver user info."}, status=400)

            email = user_data.get("response", {}).get("email")
            common_user = self.get_or_create_common_user(email)

            if common_user:
                if hasattr(common_user, "userinfo"):
                    common_user.last_login = timezone.now()
                    common_user.save()
                    access_token_jwt = create_access_token(common_user)
                    refresh_token = create_refresh_token(common_user)
                    response = NaverLoginResponse(
                        message="Login successful.",
                        access_token=access_token_jwt,
                        refresh_token=refresh_token,
                        token_type="bearer",
                        common_user_id=common_user.common_user_id,
                        email=common_user.email,
                        name=common_user.userinfo.name,
                        join_type=common_user.join_type,
                        )
                    return JsonResponse(response.model_dump(), status=200)

                return JsonResponse(
                    {
                        "message": "Additional information required.",
                        "email": email,
                    },
                    status=202,
                )

            return JsonResponse({"message": "Failed to create user."}, status=400)

        except Exception as e:
            return JsonResponse({"message": "Server error", "error": str(e)}, status=500)

    def get_naver_user_info(self, access_token: str) -> Optional[dict[str, Any]]:
        url = settings.NAVER_USER_INFO_URL
        headers = {"Authorization": f"Bearer {access_token}"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None

    def get_or_create_common_user(self, email: str) -> Optional[CommonUser]:
        common_user = CommonUser.objects.filter(email=email).first()
        if not common_user:
            common_user = CommonUser.objects.create(
                email=email,
                join_type="normal",
                is_active=True,
            )
            create_dummy_password(common_user)
        return common_user
