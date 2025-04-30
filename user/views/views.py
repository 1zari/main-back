import json
from datetime import datetime
from jwt import decode as jwt_decode, ExpiredSignatureError, InvalidTokenError
import jwt
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.views import View
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
    UserInfoUpdateResponse,
    UserInfoUpdateRequest,
    UserJoinResponseModel,
    UserLoginRequest,
    UserLoginResponse,
    UserSignupRequest, UserInfoResponse,
)
from user.services.token import create_access_token, create_refresh_token
from utils.common import get_valid_company_user, get_valid_normal_user

User = get_user_model()


class CommonUserCreateView(View):
    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            body = json.loads(request.body.decode())
            data = CommonUserBaseModel(**body)

            # 중복 체크
            if User.objects.filter(email=data.email).exists():
                return JsonResponse(
                    {"message": "이미 등록된 이메일입니다."}, status=400
                )

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
                {"message": "입력 오류", "errors": e.errors()}, status=422
            )
        except Exception as e:
            return JsonResponse(
                {"message": "서버 오류", "error": str(e)}, status=500
            )


class UserSignupView(View):
    # 일반 사용자 회원가입
    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            body = json.loads(request.body.decode())
            signup_data = UserSignupRequest(**body)  #

            # CommonUser 존재 여부 확인
            try:
                user = CommonUser.objects.get(
                    common_user_id=signup_data.common_user_id
                )
            except CommonUser.DoesNotExist:
                return JsonResponse(
                    {"message": "유저를 찾을 수 없습니다."}, status=400
                )

            # 이미 UserInfo가 존재하는지 확인
            if UserInfo.objects.filter(common_user=user).exists():
                return JsonResponse(
                    {"message": "이미 가입된 사용자입니다."}, status=400
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
            return JsonResponse(
                {"message": "잘못된 입력", "errors": e.errors()}, status=422
            )
        except Exception as e:
            return JsonResponse(
                {"message": "서버 오류", "error": str(e)}, status=500
            )


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

            if not user or not user.is_active or user.join_type != "normal":
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
                payload = jwt_decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
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
                message="회원 정보 조회 성공",
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
            return JsonResponse({"message": "유저를 찾을 수 없습니다."}, status=404)
        except PermissionDenied as e:
            return JsonResponse({"message": str(e)}, status=403)
        except Exception as e:
            return JsonResponse({"message": "서버 오류", "detail": str(e)}, status=500)

class UserInfoUpdateView(View):
    def patch(self, request, *args, **kwargs):
        try:
            #  토큰 파싱
            auth_header = request.META.get("HTTP_AUTHORIZATION")
            if not auth_header or not auth_header.startswith("Bearer "):
                raise PermissionDenied("Authentication is required.")

            token = auth_header.split(" ")[1]
            try:
                payload = jwt_decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
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
                message="회원 정보가 성공적으로 수정되었습니다.",
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
            return JsonResponse(
                {"message": "서버 오류", "detail": str(e)}, status=500
            )


class LogoutView(View):
    def post(self, request, *args, **kwargs) -> JsonResponse:
        try:
            body = json.loads(request.body.decode())
            logout_data = LogoutRequest(**body)
            refresh_token = logout_data.refresh_token
            if not refresh_token:
                return JsonResponse(
                    {"message": "Refresh token이 필요합니다."}, status=400
                )

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
                    return JsonResponse(
                        {"message": "이미 만료된 토큰입니다."}, status=400
                    )
                # Redis에 블랙리스트 등록
                r.setex(f"blacklist:refresh:{refresh_token}", ttl, "true")

                return JsonResponse(
                    LogoutResponse(message="로그아웃 성공").model_dump(),
                    status=200,
                )
            else:
                return JsonResponse(
                    {"message": "유효하지 않은 토큰 페이로드입니다."},
                    status=400,
                )

        except jwt.ExpiredSignatureError:
            return JsonResponse(
                {"message": "토큰이 이미 만료되었습니다."}, status=400
            )
        except jwt.InvalidTokenError:
            return JsonResponse(
                {"message": "유효하지 않은 토큰입니다."}, status=400
            )
        except Exception as e:
            return JsonResponse(
                {"message": "서버 오류", "error": str(e)}, status=500
            )


# 일반 유저 이메일 찾기
def find_user_email(request):
    try:
        body = json.loads(request.body.decode())
        request_data = FindUserEmailRequest(**body)
        phone_number = request_data.phone_number
        user_info = UserInfo.objects.get(phone_number=phone_number)
        common_user = user_info.common_user

        response_data = FindUserEmailResponse(email=common_user.email)
        return JsonResponse(response_data.model_dump())
    except UserInfo.DoesNotExist:
        return JsonResponse(
            {"message": "해당 전화번호로 가입된 사용자가 없습니다."}, status=404
        )
    except json.JSONDecodeError:
        return JsonResponse({"error": "잘못된 요청 형식입니다."}, status=400)
    except ValidationError as e:
        return JsonResponse(
            {
                "message": "유효하지 않은 요청 데이터입니다.",
                "errors": e.errors(),
            },
            status=400,
        )


# 일반 유저 비밀번호 재설정
def reset_user_password(request) -> JsonResponse:
    try:
        body = json.loads(request.body.decode())
        request_data = ResetUserPasswordRequest(**body)
        email = request_data.email
        phone_number = request_data.phone_number
        new_password = request_data.new_password

        try:
            # 이메일과 전화번호로 유저 정보 조회
            user_info = UserInfo.objects.get(phone_number=phone_number)
            common_user = user_info.common_user

            # 이메일이 일치하는지 확인
            if common_user.email != email:
                return JsonResponse(
                    {
                        "message": "입력한 이메일과 전화번호가 일치하지 않습니다."
                    },
                    status=400,
                )

            # 새 비밀번호 해싱 후 저장
            common_user.password = make_password(new_password)
            common_user.save()

            response_data = ResetUserPasswordResponse(
                message="비밀번호 재설정 완료"
            )
            return JsonResponse(response_data.model_dump())

        except UserInfo.DoesNotExist:
            return JsonResponse(
                {"message": "해당 전화번호로 가입된 사용자가 없습니다."},
                status=404,
            )
    except json.JSONDecodeError:
        return JsonResponse({"error": "잘못된 요청 형식입니다."}, status=400)
    except ValidationError as e:
        return JsonResponse(
            {
                "message": "유효하지 않은 요청 데이터입니다.",
                "errors": e.errors(),
            },
            status=400,
        )


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
            return JsonResponse(
                {"message": "회원 탈퇴가 완료되었습니다."}, status=200
            )

        except CommonUser.DoesNotExist:
            return JsonResponse({"message": "사용자를 찾을 수 없습니다."}, status=404)
        except jwt.ExpiredSignatureError:
            return JsonResponse({"message": "토큰이 만료되었습니다."}, status=403)
        except jwt.InvalidTokenError:
            return JsonResponse({"message": "유효하지 않은 토큰입니다."}, status=403)
        except PermissionDenied as e:
            return JsonResponse({"message": str(e)}, status=403)
        except Exception as e:
            return JsonResponse(
                {"message": "탈퇴 중 오류가 발생했습니다.", "error": str(e)}, status=500
            )

