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
from utils.common import get_valid_company_user, get_valid_normal_user

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
            # JWT 토큰에서 사용자 인증 정보 추출
            auth_header = request.META.get("HTTP_AUTHORIZATION")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise PermissionDenied("Authentication is required.")

            token = auth_header.split(" ")[1]

            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=settings.JWT_ALGORITHM,
            )

            user_id = payload.get("sub")
            if not user_id:
                raise PermissionDenied("Invalid token.")

            # JWT에서 유저 정보를 추출하여 CommonUser 객체 가져오기
            common_user = CommonUser.objects.get(common_user_id=user_id)

            # 'normal' 또는 'company' 유저에 대한 처리
            if common_user.join_type == "normal":
                # 정상 사용자 처리
                user_info = get_valid_normal_user(common_user)  # 정상 유저 정보 가져오기
                user_info.delete()  # 정상 유저 정보 삭제
                common_user.delete()  # 기본 사용자 삭제

            elif common_user.join_type == "company":
                # 기업 사용자 처리
                company_info = get_valid_company_user(common_user)  # 기업 유저 정보 가져오기
                company_info.delete()  # 기업 정보 삭제
                common_user.delete()  # 기본 사용자 삭제

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
