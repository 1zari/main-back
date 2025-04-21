import json
from datetime import datetime, timedelta
from typing import Any, Dict

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views import View
from pydantic import ValidationError

from user.redis import r
from user.schemas import TokenRefreshRequest

User = get_user_model()


def create_access_token(user):
    # access_token 발급

    expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    expiration = datetime.now() + timedelta(minutes=expire_minutes)
    payload = {
        "sub": str(user.id),  # common_user_id
        "join_type": user.join_type,
        "is_active": user.is_active,
        "exp": expiration,
    }
    return jwt.encode(payload, settings.SECRET_KEY, settings.JWT_ALGORITHM)


def create_refresh_token(user):
    # refresh_token 발급
    expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    expiration = datetime.now() + timedelta(days=expire_days)
    payload = {
        "sub": str(user.id),
        "join_type": user.join_type,
        "is_active": user.is_active,
        "exp": expiration,
    }
    return jwt.encode(payload, settings.SECRET_KEY, settings.JWT_ALGORITHM)


class TokenRefreshService:
    def __init__(self, refresh_token: str):
        self.refresh_token = refresh_token
        self.secret_key = settings.SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM

    def refresh(self) -> Dict[str, Any]:
        """
        Refresh Token을 검증하고 새로운 Access Token발급
        """
        try:
            # Refresh Token 검증
            try:
                payload = jwt.decode(
                    self.refresh_token,
                    self.secret_key,
                    algorithms=[self.algorithm],
                )
                user_id = payload["sub"]
                # 1. 블랙리스트 체크
                if r.get(f"blacklist:refresh:{self.refresh_token}"):
                    return {
                        "success": False,
                        "message": "Refresh token is blacklisted. Please log in again.",
                        "status_code": 401,
                    }

                try:
                    user = User.objects.get(common_user_id=user_id)
                except User.DoesNotExist:
                    return {
                        "success": False,
                        "message": "User not found.",
                        "status_code": 404,
                    }

                # is_active = False일때
                if not user.is_active:
                    return {
                        "success": False,
                        "message": "Inactive user. Please contact support.",
                        "status_code": 403,
                    }
            except jwt.ExpiredSignatureError:
                return {
                    "success": False,
                    "message": "Refresh token has expired.",
                    "status_code": 401,
                }
            except jwt.InvalidTokenError:
                return {
                    "success": False,
                    "message": "Invalid refresh token.",
                    "status_code": 400,
                }

                # 새로운 Access Token 발급
            new_access_token = create_access_token(user)

            return {
                "success": True,
                "access_token": new_access_token,
                "message": "Access token refreshed successfully.",
                "status_code": 200,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Server error: {str(e)}",
                "status_code": 500,
            }


# access 토큰 만료시 refresh토큰으로 새로운 access 토큰 발급
class TokenRefreshView(View):
    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            body = json.loads(request.body.decode())
            refresh_token_data = TokenRefreshRequest(**body)

            # 유효한 refresh_token을 사용하여 새로운 access_token 발급
            refresh_token = refresh_token_data.refresh_token
            token_service = TokenRefreshService(refresh_token)
            result = token_service.refresh()

            if not result["success"]:
                return JsonResponse(
                    {"message": result["message"]},
                    status=result.get("status_code", 400),
                )

            return JsonResponse(
                {
                    "access_token": result["access_token"],
                    "token_type": "Bearer",
                    "message": result["message"],
                },
                status=result.get("status_code", 200),
            )

        except ValidationError as e:
            return JsonResponse(
                {"message": "Invalid request data", "errors": e.errors()},
                status=400,
            )
        except Exception as e:
            return JsonResponse(
                {"message": "서버 오류", "error": str(e)},
                status=500,
            )
