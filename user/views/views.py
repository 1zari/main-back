import json
from datetime import datetime

import jwt
import requests
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.views import View
from pydantic import ValidationError

from user.models import CommonUser, CompanyInfo, UserInfo
from user.redis import r
from user.schemas import (
    CommonUserBaseModel,
    CommonUserResponseModel,
    CompanyInfoModel,
    CompanyJoinResponseModel,
    CompanyLoginRequest,
    CompanyLoginResponse,
    CompanySignupRequest,
    LogoutRequest,
    UserInfoModel,
    UserJoinResponseModel,
    UserLoginRequest,
    UserLoginResponse,
    UserSignupRequest,
)

from .views_token import create_access_token, create_refresh_token

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

            user = CommonUser.objects.get(
                common_user_id=signup_data.common_user_id
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

            user = CommonUser.objects.get(
                common_user_id=signup_data.common_user_id
            )

            # 이미 UserInfo가 존재하는지 확인
            if CompanyInfo.objects.filter(common_user=user).exists():
                return JsonResponse(
                    {"message": "이미 가입된 사용자입니다."}, status=400
                )

            # CompanyInfo 생성
            company_info = CompanyInfo.objects.create(
                common_user=user,
                **signup_data.model_dump(exclude={"email", "password"}),
            )

            response = CompanyJoinResponseModel(
                message="Company registration successful.",
                common_user=CommonUserResponseModel(
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

            if not user or not user.is_active or user.join_type != "user":
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

            if not user or not user.is_active or user.join_type != "company":
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


class LogoutView(View):
    def post(self, request, *args, **kwargs):
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
                refresh_token, settings.JWT_SECRET_KEY, algorithms=["HS256"]
            )
            exp = decoded.get("exp")
            now = datetime.now().timestamp()
            ttl = int(exp - now)

            if ttl <= 0:
                return JsonResponse(
                    {"message": "이미 만료된 토큰입니다."}, status=400
                )

            # Redis에 블랙리스트 등록
            r.setex(f"blacklist:refresh:{refresh_token}", ttl, "true")

            return JsonResponse({"message": "로그아웃 성공"}, status=200)

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


def create_dummy_password(common_user):
    dummy_password = CommonUser.objects.make_random_password()
    common_user.set_password(dummy_password)
    common_user.save()
    return dummy_password


class KakaoLoginView(View):
    def post(self, request, *args, **kwargs):
        try:
            body = json.loads(request.body.decode())
            authorization_code = body.get("authorization_code")

            if not authorization_code:
                return JsonResponse(
                    {"message": "authorization_code가 필요합니다."}, status=400
                )

            # 카카오 토큰 발급 API 호출
            kakao_token_url = "https://kauth.kakao.com/oauth/token"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded;charset=utf-8"
            }
            data = {
                "grant_type": "authorization_code",
                "client_id": settings.KAKAO_CLIENT_ID,
                "client_secret": settings.KAKAO_SECRET,
                "redirect_uri": settings.KAKAO_REDIRECT_URL,
                "code": authorization_code,
            }

            response = requests.post(
                kakao_token_url, headers=headers, data=data
            )
            if response.status_code != 200:
                return JsonResponse({"message": "카카오 인증 실패"}, status=400)

            # access_token 받은 후
            access_token = response.json().get("access_token")

            # 사용자 정보 요청
            user_info_response = requests.post(
                "https://kapi.kakao.com/v2/user/me",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-type": "application/x-www-form-urlencoded;charset=utf-8",
                },
            )

            if user_info_response.status_code != 200:
                return JsonResponse(
                    {"message": "카카오 사용자 정보 요청 실패"}, status=400
                )

            user_data = user_info_response.json()
            email = user_data.get("kakao_account", {}).get("email")

            # 이메일로 기존 사용자 찾기
            common_user = CommonUser.objects.filter(email=email).first()

            if not common_user:
                # 새 사용자라면 CommonUser 생성
                common_user = CommonUser.objects.create(
                    email=email,
                    join_type="user",
                    is_active=True,
                )
                dummy_password = create_dummy_password(common_user)

            # JWT 토큰 발급 (common_user 사용)
            access_token = create_access_token(common_user)
            refresh_token = create_refresh_token(common_user)

            response = {
                "message": "로그인 성공",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }

            return JsonResponse(response, status=200)

        except Exception as e:
            return JsonResponse(
                {"message": "서버 오류", "error": str(e)}, status=500
            )


class NaverLoginView(View):
    def post(self, request, *args, **kwargs):
        try:
            body = json.loads(request.body.decode())
            authorization_code = body.get("authorization_code")

            if not authorization_code:
                return JsonResponse(
                    {"message": "authorization_code가 필요합니다."}, status=400
                )

            # 네이버에서 액세스 토큰을 발급받기 위한 URL과 파라미터
            naver_token_url = "https://nid.naver.com/oauth2.0/token"

            # 인가 코드를 사용해 액세스 토큰을 요청
            token_data = {
                "grant_type": "authorization_code",
                "client_id": settings.NAVER_CLIENT_ID,
                "client_secret": settings.NAVER_SECRET,
                "code": authorization_code,
                "redirect_uri": settings.NAVER_REDIRECT_URL,
            }

            token_response = requests.post(naver_token_url, data=token_data)
            token_info = token_response.json()

            access_token = token_info.get("access_token")

            if not access_token:
                return JsonResponse(
                    {"message": "액세스 토큰 발급 실패"}, status=400
                )

            # 네이버 API 호출하여 사용자 정보 가져오기
            naver_api_url = "https://openapi.naver.com/v1/nid/me"
            headers = {"Authorization": f"Bearer {access_token}"}

            user_response = requests.get(naver_api_url, headers=headers)
            if user_response.status_code != 200:
                return JsonResponse({"message": "네이버 인증 실패"}, status=400)

            # 사용자 정보 요청
            naver_api_url = "https://openapi.naver.com/v1/nid/me"
            headers = {"Authorization": f"Bearer {access_token}"}

            user_response = requests.get(naver_api_url, headers=headers)
            if user_response.status_code != 200:
                return JsonResponse(
                    {"message": "네이버 사용자 정보 요청 실패"}, status=400
                )
            # 네이버 API에서 사용자 정보 추출
            user_data = user_response.json()
            email = user_data.get("response", {}).get("email")

            # 이메일로 기존 사용자 찾기
            common_user = CommonUser.objects.filter(email=email).first()

            if not common_user:
                # 새 사용자라면 CommonUser 생성 (비밀번호 추가)
                common_user = CommonUser.objects.create(
                    email=email,
                    join_type="user",
                    is_active=True,
                )
                dummy_password = create_dummy_password(common_user)

            # JWT 토큰 발급
            access_token = create_access_token(common_user)
            refresh_token = create_refresh_token(common_user)

            response = {
                "message": "로그인 성공",
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
            }

            return JsonResponse(response, status=200)

        except Exception as e:
            return JsonResponse(
                {"message": "서버 오류", "error": str(e)}, status=500
            )
