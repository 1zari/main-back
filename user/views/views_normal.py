import json
from datetime import datetime

import jwt
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from jwt import ExpiredSignatureError, InvalidTokenError
from jwt import decode as jwt_decode
from pydantic import ValidationError

from user.models import CommonUser, UserInfo
from user.redis import r
from user.schemas import (
    CommonUserBaseModel,
    CommonUserResponseModel,
    FindUserEmailRequest,
    FindUserEmailResponse,
    LogoutRequest,
    LogoutResponse,
    ResetUserPasswordRequest,
    ResetUserPasswordResponse,
    UserInfoModel,
    UserInfoResponse,
    UserInfoUpdateRequest,
    UserInfoUpdateResponse,
    UserJoinResponseModel,
    UserLoginRequest,
    UserLoginResponse,
    UserSignupRequest,
)
from user.services.token import create_access_token, create_refresh_token
from utils.common import get_valid_company_user, get_valid_normal_user

User = get_user_model()


@method_decorator(csrf_exempt, name="dispatch")
class UserSignupView(View):
    # 일반 사용자 회원가입
    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            body = json.loads(request.body.decode())
            signup_data = UserSignupRequest(**body)  #

            # CommonUser 존재 여부 확인
            try:
                user = CommonUser.objects.get(common_user_id=signup_data.common_user_id)
            except CommonUser.DoesNotExist:
                return JsonResponse({"message": "User not found."}, status=400)

            # 이미 UserInfo가 존재하는지 확인
            if UserInfo.objects.filter(common_user=user).exists():
                return JsonResponse({"message": "User already registered."}, status=400)

            # UserInfo 생성
            user_info = UserInfo.objects.create(
                common_user=user,
                name=signup_data.name,
                phone_number=signup_data.phone_number,
                gender=signup_data.gender,
                birthday=signup_data.birthday,
                interest=signup_data.interest,
                purpose_subscription=signup_data.purpose_subscription,
                route=signup_data.route,
            )

            # 응답
            response = UserJoinResponseModel(
                message="User registration successful.",
                common_user=CommonUserResponseModel(
                    common_user_id=user.common_user_id,
                    email=user.email,
                    join_type=user.join_type,
                ),
                user_info=UserInfoModel(
                    user_id=user_info.user_id,
                    name=user_info.name,
                    phone_number=user_info.phone_number,
                    gender=user_info.gender,
                    birthday=user_info.birthday,
                    interest=user_info.interest,
                    purpose_subscription=user_info.purpose_subscription,
                    route=user_info.route,
                ),
            )
            return JsonResponse(response.model_dump(), status=201)

        except ValidationError as e:
            return JsonResponse({"message": "Invalid input", "errors": e.errors()}, status=422)
        except Exception as e:
            return JsonResponse({"message": "Server error", "error": str(e)}, status=500)


class UserLoginView(View):
    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            body = json.loads(request.body.decode())
            login_data = UserLoginRequest(**body)

            # 사용자 인증
            user = authenticate(username=login_data.email, password=login_data.password)

            if not user or not user.is_active or user.join_type != "normal":
                return JsonResponse(
                    {"message": "Invalid email or password."},
                    status=400,
                )

            access_token = create_access_token(user)
            refresh_token = create_refresh_token(user)

            # 사용자 정보 포함 응답 생성
            response_data = {
                "message": "Login successful.",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": {
                    "common_user_id": str(user.common_user_id),
                    "email": user.email,
                    "name": user.userinfo.name,
                    "join_type": user.join_type,
                },
            }

            response = UserLoginResponse(**response_data)
            return JsonResponse(response.model_dump(), status=200)

        except ValidationError as e:
            return JsonResponse({"message": "Invalid input", "errors": e.errors()}, status=422)
        except Exception as e:
            return JsonResponse({"message": "Server error", "error": str(e)}, status=500)


class UserInfoDetailView(View):  # 유저 정보 조회
    def get(self, request, *args, **kwargs) -> JsonResponse:
        try:
            # 토큰 추출
            auth_header = request.META.get("HTTP_AUTHORIZATION")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise PermissionDenied("Authentication is required.")

            token = auth_header.split(" ")[1]

            # JWT 디코딩
            try:
                payload = jwt_decode(
                    token,
                    settings.JWT_SECRET_KEY,
                    algorithms=[settings.JWT_ALGORITHM],
                )
            except ExpiredSignatureError:
                raise PermissionDenied("Token has expired.")
            except InvalidTokenError:
                raise PermissionDenied("Invalid token.")

            user_id = payload.get("sub")
            if not user_id:
                raise PermissionDenied("Invalid token payload.")

            # CommonUser 조회
            user = CommonUser.objects.get(common_user_id=user_id)

            # UserInfo 조회
            user_info = get_valid_normal_user(user)

            #  응답 생성
            response = UserInfoResponse(
                message="User info retrieved successfully.",
                name=user_info.name,
                phone_number=user_info.phone_number,
                gender=user_info.gender,
                birthday=user_info.birthday,
                interest=user_info.interest,
                purpose_subscription=user_info.purpose_subscription,
                route=user_info.route,
            )
            return JsonResponse(response.model_dump(), status=200)

        except CommonUser.DoesNotExist:
            return JsonResponse({"message": "User not found."}, status=404)
        except PermissionDenied as e:
            return JsonResponse({"message": str(e)}, status=403)
        except Exception as e:
            return JsonResponse({"message": "Server error", "detail": str(e)}, status=500)


class UserInfoUpdateView(View):
    def patch(self, request, *args, **kwargs):
        try:
            #  토큰 파싱
            auth_header = request.META.get("HTTP_AUTHORIZATION")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise PermissionDenied("Authentication is required.")

            token = auth_header.split(" ")[1]
            try:
                payload = jwt_decode(
                    token,
                    settings.JWT_SECRET_KEY,
                    algorithms=[settings.JWT_ALGORITHM],
                )
            except ExpiredSignatureError:
                raise PermissionDenied("Token has expired.")
            except InvalidTokenError:
                raise PermissionDenied("Invalid token.")

            user_id = payload.get("sub")
            if not user_id:
                raise PermissionDenied("Invalid token payload.")

            #  공통 유저 가져오기
            user = CommonUser.objects.get(common_user_id=user_id)

            #  유저 정보 가져오기
            user_info = get_valid_normal_user(user)

            #  요청 본문 파싱
            body = json.loads(request.body)
            data = UserInfoUpdateRequest(**body)

            #  필드 수정
            for field, value in data.model_dump(exclude_unset=True).items():
                setattr(user_info, field, value)

            user_info.save()

            response = UserInfoUpdateResponse(
                message="User info successfully updated.",
                name=user_info.name,
                phone_number=user_info.phone_number,
                gender=user_info.gender,
                birthday=user_info.birthday,
                interest=user_info.interest,
                purpose_subscription=user_info.purpose_subscription,
                route=user_info.route,
            )
            return JsonResponse(response.model_dump(), status=200)

        except PermissionDenied as e:
            return JsonResponse({"message": str(e)}, status=403)
        except Exception as e:
            return JsonResponse({"message": "Server error", "detail": str(e)}, status=500)


# 일반 유저 이메일 찾기 - 클래스 기반 뷰로 변경
class UserFindEmailView(View):
    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            body = json.loads(request.body.decode())
            request_data = FindUserEmailRequest(**body)
            phone_number = request_data.phone_number
            name = request_data.name
            user_info = UserInfo.objects.get(phone_number=phone_number, name=name)
            common_user = user_info.common_user

            response_data = FindUserEmailResponse(email=common_user.email)
            return JsonResponse(response_data.model_dump())
        except UserInfo.DoesNotExist:
            return JsonResponse(
                {"message": "No user found with the provided phone number and email."},
                status=404,
            )
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid request format."}, status=400)
        except ValidationError as e:
            return JsonResponse(
                {
                    "message": "Invalid request data.",
                    "errors": e.errors(),
                },
                status=400,
            )


# 일반 유저 비밀번호 재설정 - 클래스 기반 뷰로 변경
class UserResetPasswordView(View):
    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            body = json.loads(request.body.decode())
            request_data = ResetUserPasswordRequest(**body)
            email = request_data.email
            phone_number = request_data.phone_number
            new_password = request_data.new_password

            try:
                user_info = UserInfo.objects.get(phone_number=phone_number)
                common_user = user_info.common_user

                if common_user.email != email:
                    return JsonResponse(
                        {"message": "Email and phone number do not match."},
                        status=400,
                    )

                common_user.password = make_password(new_password)
                common_user.save()

                response_data = ResetUserPasswordResponse(message="Password reset successful.")
                return JsonResponse(response_data.model_dump())

            except UserInfo.DoesNotExist:
                return JsonResponse(
                    {"message": "No user registered with this phone number."},
                    status=404,
                )
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid request format."}, status=400)
        except ValidationError as e:
            return JsonResponse(
                {
                    "message": "Invalid request data.",
                    "errors": e.errors(),
                },
                status=400,
            )
