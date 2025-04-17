import json
import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict

import jwt
import requests
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.views import View
from pydantic import ValidationError

from user.models import CompanyInfo, UserInfo
from user.schemas import (
    CommonUserCreateModel,
    CommonUserModel,
    CompanyInfoCreateModel,
    CompanyInfoModel,
    CompanyJoinResponseModel,
    CompanyLoginRequest,
    CompanyLoginResponse,
    UserInfoCreateModel,
    UserInfoModel,
    UserSignupRequest,
    CompanySignupRequest,
    UserJoinResponseModel,
    UserLoginRequest,
    UserLoginResponse,
)

User = get_user_model()


class UserSignupView(View):
    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            body = json.loads(request.body.decode())
            signup_data = UserSignupRequest(**body)  #

            # 이메일 중복 확인
            if User.objects.filter(email=signup_data.email).exists():
                return JsonResponse(
                    {"message": "이메일이 이미 사용 중입니다."}, status=400
                )

            # CommonUser 생성
            user = User.objects.create(
                email=signup_data.email,
                password=make_password(signup_data.password),
                join_type="user",
            )

            # 문자 인증 발송
            result = self.send_verification_code(signup_data.phone_number)
            if not result["success"]:
                user.delete()  # 오류 시 유저 삭제
                return JsonResponse(
                    {"message": "문자 전송 실패", "error": result["response"]},
                    status=500,
                )

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
                common_user=CommonUserModel(
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
                    purpose_subscription=signup_data.purpose_subscription,
                    route=signup_data.route,
                ),
            )
            return JsonResponse(response.model_dump(), status=201)

        except ValidationError as e:
            return JsonResponse(
                {"message": "잘못된 입력", "errors": e.errors()}, status=422
            )
        except Exception as e:
            return JsonResponse(
                {"message": "서버 오류", "error": str(e)}, status=500
            )


class CompanySignupView(View):
    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            body = json.loads(request.body.decode())
            signup_data = CompanySignupRequest(**body)

            # 이메일 중복 확인
            if User.objects.filter(email=signup_data.email).exists():
                return JsonResponse(
                    {"message": "이메일이 이미 사용 중입니다."}, status=400
                )

            # CommonUser 생성
            user = User.objects.create(
                email=signup_data.email,
                password=make_password(signup_data.password),
                join_type="company",
            )

            # CompanyInfo 생성
            company_info = CompanyInfo.objects.create(
                common_user=user,
                **signup_data.model_dump(
                    exclude={"email", "password"}
                ),
            )

            response = CompanyJoinResponseModel(
                message="Company registration successful.",
                common_user=CommonUserModel(
                    common_user_id=user.common_user_id,
                    email=user.email,
                    join_type=user.join_type,
                ),
                company_info=CompanyInfoModel(
                    company_id=company_info.company_id,
                    **signup_data.model_dump(),
                ),
            )
            return JsonResponse(response.model_dump(), status=201)

        except ValidationError as e:
            return JsonResponse(
                {"message": "잘못된 입력", "errors": e.errors()}, status=422
            )
        except Exception as e:
            return JsonResponse(
                {"message": "서버 오류", "error": str(e)}, status=500
            )


def send_verification_code(phone_number: str) -> Dict[str, Any]:
    """
    인증번호를 생성하고 해당 번호로 문자를 전송합니다.
    :param phone_number: 수신자 전화번호
    :return: {'success': bool, 'code': str, 'response': dict}
    """
    try:
        if not phone_number:
            raise ValueError("전화번호가 없습니다.")

        verification_code = "".join(random.choices(string.digits, k=6))

        url = f"https://api-sms.cloud.toast.com/sms/v2.3/appKeys/{settings.NCP_APP_KEY}/sender/sms"
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "X-NCP-APIGW-API-KEY-ID": settings.NCP_ACCESS_KEY,
            "X-NCP-APIGW-API-KEY": settings.NCP_SECRET_KEY,
        }
        data = {
            "type": "SMS",
            "countryCode": "82",
            "from": settings.SENDER_PHONE_NUMBER,
            "contentType": "COMM",
            "content": f"[인증번호] {verification_code}를 입력해주세요.",
            "messages": [
                {
                    "to": phone_number,
                    "content": f"[인증번호] {verification_code}를 입력해주세요.",
                }
            ],
        }

        response = requests.post(url, headers=headers, data=json.dumps(data))
        result = response.json()

        if result.get("resultCode") != "0000":
            return {"success": False, "response": result}

        return {"success": True, "code": verification_code, "response": result}

    except ValueError as ve:
        return {"success": False, "response": {"error": str(ve)}}
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "response": {"error": f"Request error: {str(e)}"},
        }
    except Exception as e:
        return {
            "success": False,
            "response": {"error": f"Server error: {str(e)}"},
        }


class UserLoginView(View):
    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            body = json.loads(request.body.decode())
            login_data = UserLoginRequest(**body)

            # 사용자 인증
            user = authenticate(
                username=login_data.email, password=login_data.password
            )

            if not user or user.join_type != "user":
                return JsonResponse(
                    {"message": "이메일 또는 비밀번호가 올바르지 않습니다."},
                    status=400,
                )

            secret_key = settings.SECRET_KEY
            algorithm = settings.JWT_ALGORITHM
            expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
            access_token = self.create_access_token(user, secret_key, algorithm)
            refresh_token = self.create_refresh_token(
                user, secret_key, algorithm
            )

            # 응답 데이터 생성
            response = UserLoginResponse(
                message="로그인 성공",
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
            )
            return JsonResponse(response.model_dump(), status=200)

        except ValidationError as e:
            return JsonResponse(
                {"message": "잘못된 입력", "errors": e.errors()}, status=422
            )
        except Exception as e:
            return JsonResponse(
                {"message": "서버 오류", "error": str(e)}, status=500
            )

    def create_access_token(self, user, secret_key, algorithm) -> str:
        expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        payload = {
            "sub": str(user.id),  # 사용자 ID를 토큰에 포함
            "join_type": user.join_type,
            "exp": datetime.now() + timedelta(minutes=expire_minutes),
        }
        return jwt.encode(payload, secret_key, algorithm=algorithm)

    def create_refresh_token(self, user, secret_key, algorithm) -> str:
        expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
        expiration = datetime.now() + timedelta(days=expire_days)
        payload = {
            "sub": str(user.id),  # common_user_id
            "join_type": user.join_type,
            "exp": expiration,
        }
        return jwt.encode(payload, secret_key, algorithm=algorithm)


class CompanyLoginView(View):
    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            body = json.loads(request.body.decode())
            login_data = CompanyLoginRequest(**body)

            # 사용자 인증
            user = authenticate(
                username=login_data.email, password=login_data.password
            )

            if not user or user.join_type != "company":
                return JsonResponse(
                    {"message": "이메일 또는 비밀번호가 올바르지 않습니다."},
                    status=400,
                )

            secret_key = settings.SECRET_KEY
            algorithm = settings.JWT_ALGORITHM
            expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
            access_token = self.create_access_token(user, secret_key, algorithm)
            refresh_token = self.create_refresh_token(
                user, secret_key, algorithm
            )

            # 응답 데이터 생성
            response = CompanyLoginResponse(
                message="로그인 성공",
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
            )
            return JsonResponse(response.model_dump(), status=200)

        except ValidationError as e:
            return JsonResponse(
                {"message": "잘못된 입력", "errors": e.errors()}, status=422
            )
        except Exception as e:
            return JsonResponse(
                {"message": "서버 오류", "error": str(e)}, status=500
            )

    def create_access_token(self, user, secret_key, algorithm) -> str:
        expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        payload = {
            "sub": str(user.id),
            "join_type": user.join_type,
            "exp": datetime.now() + timedelta(minutes=expire_minutes),
        }
        return jwt.encode(payload, secret_key, algorithm=algorithm)

    def create_refresh_token(self, user, secret_key, algorithm) -> str:
        expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
        expiration = datetime.now() + timedelta(days=expire_days)
        payload = {
            "sub": str(user.id),  # common_user_id
            "join_type": user.join_type,
            "exp": expiration,
        }
        return jwt.encode(payload, secret_key, algorithm=algorithm)


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
            new_access_token = self.create_access_token(user)

            return {
                "success": True,
                "access_token": new_access_token,
                "message": "Access token refreshed successfully.",
            }
        except Exception as e:
            return {"success": False, "message": f"Server error: {str(e)}"}

    def create_access_token(self, user):
        expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        expiration = datetime.now() + timedelta(minutes=expire_minutes)
        payload = {
            "sub": str(user.id),  # 사용자 ID를 토큰에 포함
            "join_type": user.join_type,
            "exp": expiration,
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)


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
