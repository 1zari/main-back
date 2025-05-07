import json
import random
import string
from urllib.parse import unquote

import requests
from django.conf import settings
from django.http import JsonResponse
from django.views import View
from pydantic import ValidationError

from user.redis import r
from user.schemas import (
    SendVerificationCodeRequest,
    VerifyBusinessRegistrationRequest,
    VerifyCodeRequest,
)


class SendVerificationCodeView(View):
    # 인증코드 생성, 발송
    def post(self, request, *args, **kwargs):

        try:
            body = json.loads(request.body.decode())
            request_data = SendVerificationCodeRequest(**body)

            phone_number = request_data.phone_number

            if not phone_number:
                return JsonResponse(
                    {"message": "Phone number is required."}, status=400
                )

            # 인증번호 생성
            verification_code = "".join(random.choices(string.digits, k=6))
            r.setex(f"verify:{phone_number}", 300, verification_code)

            # SMS API 요청
            # 알리고 API 요청 URL
            url = settings.ALIGO_API_URL
            headers = {
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            }

            # 요청에 필요한 데이터 설정
            data = {
                "api_key": settings.ALIGO_API_KEY,
                "user_id": settings.ALIGO_USER_ID,
                "sender": settings.ALIGO_SENDER,
                "receiver": phone_number,
                "msg": f"[인증번호] {verification_code}를 입력해주세요.",
                "title": "인증번호 발송",
            }

            try:
                response = requests.post(url, headers=headers, data=data)
                response.raise_for_status()  # HTTPError 발생 시 처리
                result = response.json()

                if result.get("result_code") != 1:
                    return JsonResponse(
                        {"message": "Failed to send SMS", "response": result},
                        status=400,
                    )
            except requests.exceptions.Timeout as e:
                return JsonResponse(
                    {"message": "API request timeout", "error": str(e)},
                    status=500,
                )
            except requests.exceptions.HTTPError as e:
                return JsonResponse(
                    {"message": "HTTP error", "error": str(e)},
                    status=500,
                )
            except requests.exceptions.RequestException as e:
                return JsonResponse(
                    {"message": "Aligo API request error", "error": str(e)},
                    status=500,
                )
            return JsonResponse(
                {"message": "Verification code sent successfully"}, status=200
            )

        except ValidationError as e:
            return JsonResponse(
                {"message": "Invalid request data", "errors": e.errors()},
                status=400,
            )
        except Exception as e:
            return JsonResponse(
                {"message": "Server error", "error": str(e)}, status=500
            )


class VerifyCodeView(View):
    # 인증번호 검증
    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            body = json.loads(request.body.decode())
            request_data = VerifyCodeRequest(**body)

            phone_number = request_data.phone_number
            code = request_data.code

            saved_code = r.get(f"verify:{phone_number}")
            if saved_code is None:
                return JsonResponse(
                    {"message": "Verification code has expired."}, status=400
                )

            if saved_code != code:
                return JsonResponse(
                    {"message": "Verification code does not match."}, status=400
                )

            r.delete(f"verify:{phone_number}")

            return JsonResponse(
                {"message": "Verification successful."}, status=200
            )
        except ValidationError as e:
            return JsonResponse(
                {"message": "Invalid request data", "errors": e.errors()},
                status=400,
            )
        except Exception as e:
            return JsonResponse(
                {"message": "Server error", "error": str(e)}, status=500
            )


class VerifyBusinessRegistrationView(View):
    # 사업자등록번호 검증
    def post(self, request, *args, **kwargs):
        try:
            body = json.loads(request.body.decode())
            request_data = VerifyBusinessRegistrationRequest(**body)

            b_no = request_data.b_no
            p_nm = request_data.p_nm
            start_dt = request_data.start_dt

            if not b_no or not p_nm or not start_dt:
                return JsonResponse(
                    {
                        "error": "Please provide business number, owner name, and start date."
                    },
                    status=400,
                )

            # api_key디코딩 후 사용
            api_key = unquote(settings.KOREA_TAX_API_KEY)
            if not api_key:
                return JsonResponse(
                    {"error": "API key is not configured."}, status=500
                )

            # API 엔드포인트
            url = settings.KOREA_TAX_API_URL
            params = {"serviceKey": api_key, "returnType": "JSON"}
            request_body = {
                "businesses": [
                    {"b_no": b_no, "p_nm": p_nm, "start_dt": start_dt}
                ]
            }

            response = requests.post(url, params=params, json=request_body)
            response.raise_for_status()

            result = response.json()

            if result.get("data") and result["data"][0].get("valid") == "01":
                return JsonResponse(
                    {
                        "valid": True,
                        "message": "Business information is valid.",
                    },
                    status=200,
                )
            else:
                msg = result["data"][0].get(
                    "valid_msg", "Business information is not valid."
                )
                return JsonResponse(
                    {"valid": False, "message": msg}, status=200
                )

        except json.JSONDecodeError:
            return JsonResponse(
                {"error": "Invalid request format."}, status=400
            )

        except ValidationError as e:
            return JsonResponse(
                {"message": "Invalid request data", "errors": e.errors()},
                status=400,
            )
        except Exception as e:
            return JsonResponse({"error": f"Server error: {e}"}, status=500)
