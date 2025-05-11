import json
from datetime import datetime

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from pydantic import ValidationError

from user.models import CommonUser
from user.redis import r
from user.schemas import (
    CommonUserBaseModel,
    CommonUserResponseModel,
    LogoutRequest,
    LogoutResponse,
)
from utils.common import (
    check_and_return_company_user,
    check_and_return_normal_user,
    get_user_from_token,
)

User = get_user_model()


@method_decorator(csrf_exempt, name="dispatch")
class CommonUserCreateView(View):
    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            body = json.loads(request.body.decode())
            data = CommonUserBaseModel(**body)

            # 중복 체크
            if User.objects.filter(email=data.email).exists():
                return JsonResponse({"message": "Email is already registered."}, status=400)

            # CommonUser 생성
            user = User.objects.create(
                email=data.email,
                join_type=data.join_type,
                password=make_password(data.password),
                is_active=True,
            )

            response = CommonUserResponseModel(
                common_user_id=user.common_user_id,
                email=user.email,
                join_type=user.join_type,
            )

            return JsonResponse(response.model_dump(), status=201)

        except ValidationError as e:
            return JsonResponse(
                {"message": "Validation error", "errors": e.errors()},
                status=422,
            )
        except Exception as e:
            return JsonResponse({"message": "Server error", "error": str(e)}, status=500)


class LogoutView(View):
    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            body = json.loads(request.body.decode())
            logout_data = LogoutRequest(**body)
            refresh_token = logout_data.refresh_token
            if not refresh_token:
                return JsonResponse({"message": "Refresh token is required."}, status=400)

            # 토큰 디코딩해서 남은 시간 확인
            decoded = jwt.decode(
                refresh_token,
                settings.JWT_SECRET_KEY,
                algorithms=settings.JWT_ALGORITHM,
            )
            exp = decoded.get("exp")
            if exp is not None:
                now = datetime.now().timestamp()
                ttl = int(exp - now)

                if ttl <= 0:
                    return JsonResponse({"message": "Token is already expired."}, status=400)
                # Redis에 블랙리스트 등록
                r.setex(f"blacklist:refresh:{refresh_token}", ttl, "true")

                return JsonResponse(
                    LogoutResponse(message="Logout successful.").model_dump(),
                    status=200,
                )
            else:
                return JsonResponse(
                    {"message": "Invalid token payload."},
                    status=400,
                )

        except jwt.ExpiredSignatureError:
            return JsonResponse({"message": "Token is already expired."}, status=400)
        except jwt.InvalidTokenError:
            return JsonResponse({"message": "Invalid token."}, status=400)
        except Exception as e:
            return JsonResponse({"message": "Server error", "error": str(e)}, status=500)


class UserDeleteView(View):
    def delete(self, request, *args, **kwargs) -> JsonResponse:
        try:
            valid_user: CommonUser = get_user_from_token(request)

            # 'normal' 또는 'company' 유저에 대한 처리
            if valid_user.join_type == "normal":
                user_info = check_and_return_normal_user(valid_user)  # 정상 유저 정보 가져오기
                user_info.delete()  # 정상 유저 정보 삭제
                valid_user.delete()  # 기본 사용자 삭제

            elif valid_user.join_type == "company":
                company_user = check_and_return_company_user(valid_user)
                company_user.delete()  # 기업 정보 삭제
                valid_user.delete()  # 기본 사용자 삭제

            else:
                raise PermissionDenied("Invalid user type.")

            # 성공적으로 삭제 완료
            return JsonResponse({"message": "User deletion successful."}, status=200)

        except CommonUser.DoesNotExist:
            return JsonResponse({"message": "User not found."}, status=404)
        except jwt.ExpiredSignatureError:
            return JsonResponse({"message": "Token has expired."}, status=403)
        except jwt.InvalidTokenError:
            return JsonResponse({"message": "Invalid token."}, status=403)
        except PermissionDenied as e:
            return JsonResponse({"message": str(e)}, status=403)
        except Exception as e:
            return JsonResponse(
                {
                    "message": "An error occurred during account deletion.",
                    "error": str(e),
                },
                status=500,
            )


class EmailDuplicateCheckView(View):
    def get(self, request, *args, **kwargs) -> JsonResponse:
        email = request.GET.get("email")
        if not email:
            return JsonResponse({"message": "Email is required."}, status=400)

        if User.objects.filter(email=email).exists():
            return JsonResponse({"message": "Email is already registered."}, status=200)
        else:
            return JsonResponse({"message": "Email is available."}, status=200)
