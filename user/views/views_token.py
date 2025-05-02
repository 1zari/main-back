import json

from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views import View
from pydantic import ValidationError

from user.schemas import TokenRefreshRequest
from user.services.token_refresh import TokenRefreshService

User = get_user_model()


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
                {"message": "Server error", "error": str(e)},
                status=500,
            )
