import json
import random
import string
from typing import Any, Dict

import requests
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.views import View
from pydantic import ValidationError

from user.models import CommonUser, CompanyInfo, UserInfo
from user.schemas import (
    CommonUserModel,
    CompanyInfoModel,
    CompanyJoinResponseModel,
    CompanyLoginRequest,
    CompanyLoginResponse,
    CompanySignupRequest,
    UserInfoModel,
    UserJoinResponseModel,
    UserLoginRequest,
    UserLoginResponse,
    UserSignupRequest,
)

from .views_token import create_access_token, create_refresh_token

User = get_user_model()


def create_common_user(email, password, join_type):
    return User.objects.create(
        email=email,
        password=make_password(password),
        join_type=join_type,
    )


class UserSignupView(View):
    # 일반 사용자 회원가입
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
            user = create_common_user(
                signup_data.email, signup_data.password, "user"
            )

            # 문자 인증 발송
            result = send_verification_code(signup_data.phone_number)
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
    # 기업 사용자 회원가입
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
            user = create_common_user(
                signup_data.email, signup_data.password, "company"
            )

            # CompanyInfo 생성
            company_info = CompanyInfo.objects.create(
                common_user=user,
                **signup_data.model_dump(exclude={"email", "password"}),
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
    # 일반 사용자 로그인
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

            access_token = create_access_token(user)
            refresh_token = create_refresh_token(user)

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


class CompanyLoginView(View):
    # 기업 사용자 로그인
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

            access_token = create_access_token(user)
            refresh_token = create_refresh_token(user)

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
