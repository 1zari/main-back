import json
from datetime import datetime, timedelta

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views import View
from pydantic import ValidationError

from user.schemas import TokenRefreshRequest
from user.services.token_refresh import TokenRefreshService

User = get_user_model()


def create_access_token(user):
    # access_token 발급

    expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    expiration = datetime.now() + timedelta(minutes=expire_minutes)
    payload = {
        "sub": str(user.common_user_id),  # common_user_id
        "join_type": user.join_type,
        "is_active": user.is_active,
        "exp": expiration,
    }
    return jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def create_refresh_token(user):
    # refresh_token 발급
    expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    expiration = datetime.now() + timedelta(days=expire_days)
    payload = {
        "sub": str(user.common_user_id),
        "join_type": user.join_type,
        "is_active": user.is_active,
        "exp": expiration,
    }
    return jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )

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
