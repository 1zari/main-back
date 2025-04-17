import json
from datetime import datetime, timedelta
from typing import Any, Dict

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views import View

User = get_user_model()


def create_access_token(user):
    # access_token 발급

    expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    expiration = datetime.now() + timedelta(minutes=expire_minutes)
    payload = {
        "sub": str(user.id),  # common_user_id
        "join_type": user.join_type,
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

                user = User.objects.get(id=user_id)
            except jwt.ExpiredSignatureError:
                return {
                    "success": False,
                    "message": "Refresh token has expired.",
                }
            except jwt.InvalidTokenError:
                return {"success": False, "message": "Invalid refresh token."}

            # 새로운 Access Token 발급
            new_access_token = create_access_token(user)

            return {
                "success": True,
                "access_token": new_access_token,
                "message": "Access token refreshed successfully.",
            }
        except Exception as e:
            return {"success": False, "message": f"Server error: {str(e)}"}


# access 토큰 만료시 refresh토큰으로 새로운 access 토큰 발급
class TokenRefreshView(View):
    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            body = json.loads(request.body.decode())
            refresh_token = body.get("refresh_token")

            if not refresh_token:
                return JsonResponse(
                    {"message": "Refresh token is required."}, status=400
                )

            # TokenRefreshService를 사용하여 새로운 액세스 토큰을 발급
            token_service = TokenRefreshService(refresh_token)
            result = token_service.refresh()

            if not result["success"]:
                return JsonResponse({"message": result["message"]}, status=400)

            # 새로운 액세스 토큰 반환
            return JsonResponse(
                {
                    "access_token": result["access_token"],
                    "message": result["message"],
                },
                status=200,
            )

        except Exception as e:
            return JsonResponse(
                {"message": "서버 오류", "error": str(e)}, status=500
            )
