import json
import logging

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from pydantic import ValidationError

from user.models import CommonUser, CompanyInfo
from user.schemas import (
    CommonUserResponseModel,
    CompanyInfoModel,
    CompanyInfoResponse,
    CompanyInfoUpdateRequest,
    CompanyInfoUpdateResponse,
    CompanyJoinResponseModel,
    CompanyLoginRequest,
    CompanyLoginResponse,
    CompanySignupRequest,
    FindCompanyEmailRequest,
    FindCompanyEmailResponse,
    LoginCompanyUserModel,
    ResetCompanyPasswordRequest,
    ResetCompanyPasswordResponse,
)
from user.services.token import create_access_token, create_refresh_token
from utils.common import get_user_from_token, get_valid_company_user
from utils.ncp_storage import upload_to_ncp_storage

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class CompanySignupView(View):
    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            # 📌 form-data 디버깅 로그
            logger.info("FILES: %s", request.FILES)
            logger.info("POST: %s", request.POST)

            # 1) form-data 텍스트만 가져오고, 테스트용 is_staff 제거
            data = request.POST.dict()
            data.pop("is_staff", None)

            # 2) 파일 업로드 처리
            if "certificate_image" not in request.FILES:
                return JsonResponse(
                    {"message": "Business registration certificate file is required."},
                    status=400,
                )
            cert_url = upload_to_ncp_storage(request.FILES["certificate_image"])

            logo_url = None
            if "company_logo" in request.FILES:
                logo_url = upload_to_ncp_storage(request.FILES["company_logo"])

            # 3) Pydantic 검증 (파일 URL은 뷰에서만 처리)
            signup_dto = CompanySignupRequest(**data)
            ci_data = signup_dto.model_dump(exclude={"common_user_id"})

            # 4) CommonUser 조회·중복 가입 방지
            user = CommonUser.objects.get(common_user_id=signup_dto.common_user_id)
            if CompanyInfo.objects.filter(common_user=user).exists():
                return JsonResponse(
                    {"message": "Company user is already registered."},
                    status=400,
                )

            # 5) CompanyInfo 생성
            company_info = CompanyInfo.objects.create(
                common_user=user,
                certificate_image=cert_url,
                company_logo=logo_url,
                **ci_data,
            )

            # 6) is_staff 권한 부여
            user.is_staff = True
            user.save(update_fields=["is_staff"])

            # 7) 응답 생성
            response = CompanyJoinResponseModel(
                message="Company registration successful.",
                common_user=CommonUserResponseModel(
                    common_user_id=user.common_user_id,
                    email=user.email,
                    join_type=user.join_type,
                    is_staff=user.is_staff,
                ),
                company_info=CompanyInfoModel(
                    company_id=company_info.company_id,
                    company_name=company_info.company_name,
                    establishment=company_info.establishment,
                    company_address=company_info.company_address,
                    business_registration_number=company_info.business_registration_number,
                    company_introduction=company_info.company_introduction,
                    certificate_image=cert_url,
                    company_logo=logo_url,
                    ceo_name=company_info.ceo_name,
                    manager_name=company_info.manager_name,
                    manager_phone_number=company_info.manager_phone_number,
                    manager_email=company_info.manager_email,
                ),
            )
            return JsonResponse(response.model_dump(), status=201)

        except ValidationError as e:
            return JsonResponse(
                {"message": "Input validation failed.", "errors": e.errors()},
                status=422,
            )
        except CommonUser.DoesNotExist:
            return JsonResponse({"message": "User not found."}, status=404)
        except Exception as e:
            return JsonResponse({"message": "Server error.", "error": str(e)}, status=500)


class CompanyLoginView(View):
    # 기업 사용자 로그인
    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            body = json.loads(request.body.decode())
            login_data = CompanyLoginRequest(**body)

            # 사용자 인증
            user = authenticate(username=login_data.email, password=login_data.password)

            if not user or not user.is_active or user.join_type != "company":
                return JsonResponse(
                    {"message": "Invalid email or password."},
                    status=400,
                )

            user.last_login = timezone.now()
            user.save()

            access_token = create_access_token(user)
            refresh_token = create_refresh_token(user)

            # 응답 데이터 생성

            response = CompanyLoginResponse(
                message="Login successful.",
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                user=LoginCompanyUserModel(
                    common_user_id=user.common_user_id,
                    email=user.email,
                    join_type=user.join_type,
                    company_name=user.companyinfo.company_name,
                ),
            )
            return JsonResponse(response.model_dump(), status=200)

        except ValidationError as e:
            return JsonResponse({"message": "Invalid input.", "errors": e.errors()}, status=422)
        except Exception as e:
            return JsonResponse({"message": "Server error.", "error": str(e)}, status=500)


class CompanyInfoDetailView(View):  # 기업 정보 조회
    def get(self, request, *args, **kwargs) -> JsonResponse:
        try:
            valid_user: CommonUser = get_user_from_token(request)
            company_info: CompanyInfo = get_valid_company_user(valid_user)

            response = CompanyInfoResponse(
                company_name=company_info.company_name,
                establishment=company_info.establishment,
                company_address=company_info.company_address,
                business_registration_number=company_info.business_registration_number,
                company_introduction=company_info.company_introduction,
                ceo_name=company_info.ceo_name,
                manager_name=company_info.manager_name,
                manager_phone_number=company_info.manager_phone_number,
                manager_email=company_info.manager_email,
                certificate_image=company_info.certificate_image,
                company_logo=company_info.company_logo,
                message="Company info retrieved successfully.",
            )
            return JsonResponse(response.model_dump(), status=200)

        except PermissionDenied as e:
            return JsonResponse({"message": str(e)}, status=403)
        except Exception as e:
            return JsonResponse({"message": "Server error.", "detail": str(e)}, status=500)


class CompanyInfoUpdateView(View):
    def patch(self, request, *args, **kwargs) -> JsonResponse:
        try:
            valid_user: CommonUser = get_user_from_token(request)
            company_user: CompanyInfo = get_valid_company_user(valid_user)

            body = json.loads(request.body)
            validated_data = CompanyInfoUpdateRequest(**body)

            for field, value in validated_data.model_dump(exclude_none=True).items():
                setattr(company_user, field, value)

            company_user.save()

            response_data = CompanyInfoUpdateResponse(
                message="Company info successfully updated.",
                company_name=company_user.company_name,
                establishment=company_user.establishment,
                company_address=company_user.company_address,
                business_registration_number=company_user.business_registration_number,
                company_introduction=company_user.company_introduction,
                ceo_name=company_user.ceo_name,
                manager_name=company_user.manager_name,
                manager_phone_number=company_user.manager_phone_number,
                manager_email=company_user.manager_email,
            )
            return JsonResponse(response_data.model_dump(), status=200)

        except PermissionDenied as e:
            return JsonResponse({"message": str(e)}, status=403)
        except ValidationError as e:
            return JsonResponse({"message": str(e)}, status=400)
        except Exception as e:
            return JsonResponse({"message": f"Error occurred: {str(e)}"}, status=500)


class CompanyFindEmailView(View):
    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            body = json.loads(request.body.decode())
            request_data = FindCompanyEmailRequest(**body)

            phone_number = request_data.phone_number
            business_registration_number = request_data.business_registration_number
            company_name = request_data.company_name

            # 회사 정보 존재 여부 먼저 확인
            qs = CompanyInfo.objects.filter(
                manager_phone_number=phone_number,
                company_name=company_name,
            )
            if not qs.exists():
                return JsonResponse(
                    {"message": "No registered company found with the provided phone number and company name."},
                    status=404,
                )

            company_info = qs.get()

            if company_info.business_registration_number != business_registration_number:
                return JsonResponse(
                    {"message": "The provided business registration number does not match."},
                    status=400,
                )

            response_data = FindCompanyEmailResponse(email=company_info.manager_email)
            return JsonResponse(response_data.model_dump())

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
        except Exception as e:
            return JsonResponse({"message": "Server error.", "error": str(e)}, status=500)


# 사업자 비밀번호 재설정 (클래스 기반 뷰)
class CompanyResetPasswordView(View):
    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            body = json.loads(request.body.decode())
            request_data = ResetCompanyPasswordRequest(**body)
            email = request_data.email
            phone_number = request_data.phone_number
            business_registration_number = request_data.business_registration_number
            new_password = request_data.new_password

            try:
                company_info = CompanyInfo.objects.get(manager_email=email, manager_phone_number=phone_number)

                if company_info.business_registration_number != business_registration_number:
                    return JsonResponse(
                        {"message": "The provided business registration number does not match."},
                        status=400,
                    )

                common_user = company_info.common_user
                if common_user.email != email:
                    return JsonResponse(
                        {"message": "The provided email and phone number do not match."},
                        status=400,
                    )

                common_user.password = make_password(new_password)
                common_user.save()

                response_data = ResetCompanyPasswordResponse(message="Password reset successful.")
                return JsonResponse(response_data.model_dump())

            except CompanyInfo.DoesNotExist:
                return JsonResponse(
                    {"message": "No registered company found with the provided information."},
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
        except Exception as e:
            return JsonResponse({"message": "Server error.", "error": str(e)}, status=500)
