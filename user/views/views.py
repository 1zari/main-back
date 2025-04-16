import json
import random
import string
from typing import Any, Dict

import requests
from django.contrib.auth import get_user_model
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
    UserInfoCreateModel,
    UserInfoModel,
    UserJoinResponseModel,
)

User = get_user_model()


def load_secrets():
    with open("secrets.json") as f:
        return json.load(f)


class UserSignupView(View):
    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            body = json.loads(request.body.decode())

            # 공통 유저 유효성 검사
            common_user_data = CommonUserCreateModel(**body)

            # 이메일 중복 확인
            if User.objects.filter(email=common_user_data.email).exists():
                return JsonResponse(
                    {"message": "이메일이 이미 사용 중입니다."}, status=400
                )

            # 일반 유저 추가 정보 유효성 검사
            user_info_data = UserInfoCreateModel(**body)

            # CommonUser 생성
            user = User.objects.create(
                email=common_user_data.email,
                password=make_password(common_user_data.password),
                join_type="user",
            )

            # 문자 인증 발송
            result = send_verification_code(user_info_data.phone_number)
            if not result["success"]:
                return JsonResponse(
                    {"message": "문자 전송 실패", "error": result["response"]},
                    status=500,
                )

            # UserInfo 생성
            user_info = UserInfo.objects.create(
                common_user=user,
                name=user_info_data.name,
                phone_number=user_info_data.phone_number,
                gender=user_info_data.gender,
                birthday=user_info_data.birthday,
                interest=user_info_data.interest,
                purpose_subscription=user_info_data.purpose_subscription,
                route=user_info_data.route,
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
                    purpose_subscription=user_info.purpose_subscription,
                    route=user_info.route,
                ),
            )
            return JsonResponse(response.model_dump(), status=201)

        except ValidationError as e:
            return JsonResponse(
                {"message": "Invalid input", "errors": e.errors()}, status=422
            )
        except Exception as e:
            return JsonResponse(
                {"message": "Server error", "error": str(e)}, status=500
            )


class CompanySignupView(View):
    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            body = json.loads(request.body.decode())

            # 공통 유저 유효성 검사
            common_user_data = CommonUserCreateModel(**body)

            # 이메일 중복 확인
            if User.objects.filter(email=common_user_data.email).exists():
                return JsonResponse(
                    {"message": "이메일이 이미 사용 중입니다."}, status=400
                )

            # 기업 정보 유효성 검사
            company_info_data = CompanyInfoCreateModel(**body)

            # CommonUser 생성
            user = User.objects.create(
                email=common_user_data.email,
                password=make_password(common_user_data.password),
                join_type="company",
            )

            # CompanyInfo 생성
            company_info = CompanyInfo.objects.create(
                common_user=user,
                company_name=company_info_data.company_name,
                establishment=company_info_data.establishment,
                company_address=company_info_data.company_address,
                business_registration_number=company_info_data.business_registration_number,
                company_introduction=company_info_data.company_introduction,
                certificate_image=company_info_data.certificate_image,
                company_logo=company_info_data.company_logo,
                ceo_name=company_info_data.ceo_name,
                manager_name=company_info_data.manager_name,
                manager_phone_number=company_info_data.manager_phone_number,
                manager_email=company_info_data.manager_email,
                is_staff=company_info_data.is_staff,
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
                    **company_info_data.model_dump(),
                ),
            )
            return JsonResponse(response.model_dump(), status=201)

        except ValidationError as e:
            return JsonResponse(
                {"message": "Invalid input", "errors": e.errors()}, status=422
            )
        except Exception as e:
            return JsonResponse(
                {"message": "Server error", "error": str(e)}, status=500
            )


def send_verification_code(phone_number: str) -> Dict[str, Any]:
    """
    인증번호를 생성하고 해당 번호로 문자를 전송합니다.
    :param phone_number: 수신자 전화번호
    :return: {'success': bool, 'code': str, 'response': dict}
    """
    secrets = load_secrets()
    try:
        if not phone_number:
            raise ValueError("전화번호가 없습니다.")

        verification_code = "".join(random.choices(string.digits, k=6))

        url = f"https://api-sms.cloud.toast.com/sms/v2.3/appKeys/{secrets['NCP_APP_KEY']}/sender/sms"
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "X-NCP-APIGW-API-KEY-ID": secrets["NCP_ACCESS_KEY"],
            "X-NCP-APIGW-API-KEY": secrets["NCP_SECRET_KEY"],
        }
        data = {
            "type": "SMS",
            "countryCode": "82",
            "from": secrets["SENDER_PHONE_NUMBER"],
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
