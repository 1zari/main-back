import json
from unittest.mock import patch

import pytest
from django.contrib.auth.hashers import check_password
from django.test import Client
from django.urls import reverse

from user.models import CommonUser, CompanyInfo, UserInfo
from user.views.views_token import create_access_token, create_refresh_token


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def common_user_data():
    return {
        "email": "test_user@example.com",
        "password": "testpassword123!",
        "join_type": "normal",
        "is_active": True,
    }


@pytest.fixture
def common_company_data():
    return {
        "email": "test_company@example.com",
        "password": "testpassword123!",
        "join_type": "company",
        "is_active": True,
    }


@pytest.fixture
def user_info():
    common_user = CommonUser.objects.create_user(
        email="test@example.com", password="oldpassword"
    )
    return UserInfo.objects.create(
        common_user=common_user,
        name="테스트 사용자",
        phone_number="01012345678",
        gender="M",
        birthday="1990-01-01",
    )


@pytest.fixture
def company_info():
    common_user = CommonUser.objects.create_user(
        email="company@example.com", password="oldpassword"
    )
    return CompanyInfo.objects.create(
        common_user=common_user,
        company_name="테스트 회사",
        establishment="2023-01-01",
        company_address="테스트 주소",
        business_registration_number="1234567890",
        company_introduction="테스트 소개",
        ceo_name="테스트 대표",
        manager_name="테스트 담당자",
        manager_phone_number="01087654321",
        manager_email="company@example.com",
    )


@pytest.fixture
def common_user():
    return CommonUser.objects.create_user(
        email="test_user@example.com",
        password="testpassword123!",
        join_type="normal",
    )


@pytest.fixture
def common_company():
    return CommonUser.objects.create_user(
        email="test_company@example.com",
        password="testpassword123!",
        join_type="company",
    )


@pytest.fixture
def user_token(common_user):
    return create_access_token(common_user)


@pytest.fixture
def company_token(common_company):
    return create_access_token(common_company)


@pytest.mark.django_db
def test_common_user_create(client, common_user_data):
    response = client.post(
        "/api/user/common_user/signup/",
        data=json.dumps(common_user_data),
        content_type="application/json",
    )
    assert response.status_code == 201
    assert CommonUser.objects.filter(email=common_user_data["email"]).exists()


@pytest.mark.django_db
def test_user_signup(client, common_user_data):
    # 공통 유저 생성
    common_user = CommonUser.objects.create_user(**common_user_data)

    user_signup_data = {
        "common_user_id": str(common_user.common_user_id),
        "name": "홍길동",
        "phone_number": "01012345678",
        "gender": "male",
        "birthday": "1990-01-01",
        "interest": ["AI", "Web"],
        "purpose_subscription": ["job_search"],
        "route": ["friend"],
    }

    response = client.post(
        "/api/user/signup/",
        data=json.dumps(user_signup_data),
        content_type="application/json",
    )
    assert response.status_code == 201
    assert UserInfo.objects.filter(common_user=common_user).exists()


@pytest.mark.django_db
def test_company_signup(client, common_company_data):
    common_user = CommonUser.objects.create_user(**common_company_data)

    company_signup_data = {
        "common_user_id": str(common_user.common_user_id),
        "company_name": "테스트 회사",
        "establishment": "2020-01-01",
        "company_address": "서울시 강남구",
        "business_registration_number": "123-45-67890",
        "company_introduction": "우리는 IT 기업입니다.",
        "company_logo": None,
        "certificate_image": "image_url",
        "ceo_name": "김대표",
        "manager_name": "김대표",
        "manager_phone_number": "01087654321",
        "manager_email": "corp@example.com",
        "is_staff": True,
    }

    response = client.post(
        "/api/user/company/signup/",
        data=json.dumps(company_signup_data),
        content_type="application/json",
    )
    assert response.status_code == 201
    assert CompanyInfo.objects.filter(common_user=common_user).exists()


@pytest.mark.django_db
def test_user_login(client, common_user_data):
    CommonUser.objects.create_user(**common_user_data)

    login_data = {
        "email": common_user_data["email"],
        "password": common_user_data["password"],
        "is_active": common_user_data["is_active"],
    }

    response = client.post(
        "/api/user/login/",
        data=json.dumps(login_data),
        content_type="application/json",
    )

    # 응답 로그 추가
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Content: {response.content}")

    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.django_db
def test_company_login(client, common_company_data):
    CommonUser.objects.create_user(**common_company_data)

    login_data = {
        "email": common_company_data["email"],
        "password": common_company_data["password"],
        "is_active": common_company_data["is_active"],
    }

    response = client.post(
        "/api/user/company/login/",
        data=json.dumps(login_data),
        content_type="application/json",
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.django_db
def test_logout_view(client, common_user_data):
    user = CommonUser.objects.create_user(**common_user_data)
    refresh_token = create_refresh_token(user)

    response = client.post(
        "/api/user/logout/",
        data=json.dumps({"refresh_token": refresh_token}),
        content_type="application/json",
    )

    print(f"JSON: {response.json()}")

    assert response.status_code == 200
    assert response.json()["message"] == "로그아웃 성공"


@pytest.mark.django_db
def test_find_user_email(client, user_info):
    """일반 유저 이메일 찾기 테스트 (성공/실패)"""

    # 성공
    url = reverse("user:find-user-email")
    data = {"phone_number": user_info.phone_number}
    response = client.post(
        url, json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 200  # OK
    assert response.json()["email"] == user_info.common_user.email

    # 실패
    data = {"phone_number": "01099998888"}
    response = client.post(
        url, json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 404  # Not Found


@pytest.mark.django_db
def test_reset_user_password(client, user_info):
    """일반 유저 비밀번호 재설정 테스트 (성공/실패/이메일 불일치)"""

    # 성공
    url = reverse("user:reset-user-password")
    new_password = "newsecurepassword"
    data = {
        "email": user_info.common_user.email,
        "phone_number": user_info.phone_number,
        "new_password": new_password,
    }
    response = client.post(
        url, json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 200  # OK
    user_info.common_user.refresh_from_db()
    assert check_password(new_password, user_info.common_user.password)

    # 실패 (사용자 없음)
    data = {
        "email": "test@example.com",
        "phone_number": "01099998888",
        "new_password": "newpassword",
    }
    response = client.post(
        url, json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 404  # Not Found

    # 실패 (이메일 불일치)
    data = {
        "email": "wrong@example.com",
        "phone_number": user_info.phone_number,
        "new_password": "newpassword",
    }
    response = client.post(
        url, json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 400  # Bad Request


@pytest.mark.django_db
def test_find_company_email(client, company_info):
    """사업자 이메일 찾기 테스트 (성공/실패/사업자등록번호 불일치)"""

    # 성공
    url = reverse("user:find-company-email")
    data = {
        "phone_number": company_info.manager_phone_number,
        "business_registration_number": company_info.business_registration_number,
    }
    response = client.post(
        url, json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 200  # OK
    assert response.json()["email"] == company_info.manager_email

    # 실패 (사업자 없음)
    data = {
        "phone_number": "01099998888",
        "business_registration_number": "1234567890",
    }
    response = client.post(
        url, json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 404  # Not Found

    # 실패 (사업자등록번호 불일치)
    data = {
        "phone_number": company_info.manager_phone_number,
        "business_registration_number": "9999999999",
    }
    response = client.post(
        url, json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 400  # Bad Request


@pytest.mark.django_db
def test_reset_company_password(client, company_info):
    """사업자 비밀번호 재설정 테스트 (성공/실패/사업자등록번호 불일치/이메일 불일치)"""

    # 성공
    url = reverse("user:reset-company-password")
    new_password = "newsecurepassword"
    data = {
        "email": company_info.manager_email,
        "phone_number": company_info.manager_phone_number,
        "business_registration_number": company_info.business_registration_number,
        "new_password": new_password,
    }
    response = client.post(
        url, json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 200  # OK
    company_info.common_user.refresh_from_db()
    assert check_password(new_password, company_info.common_user.password)

    # 실패 (사업자 없음)
    data = {
        "email": "company@example.com",
        "phone_number": "01099998888",
        "business_registration_number": "1234567890",
        "new_password": "newpassword",
    }
    response = client.post(
        url, json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 404  # Not Found

    # 실패 (사업자등록번호 불일치)
    data = {
        "email": company_info.manager_email,
        "phone_number": company_info.manager_phone_number,
        "business_registration_number": "9999999999",
        "new_password": "newpassword",
    }
    response = client.post(
        url, json.dumps(data), content_type="application/json"
    )
    assert response.status_code == 400  # Bad Request


@pytest.mark.django_db
@patch("utils.common.get_valid_normal_user")
def test_normal_user_delete_success(
    mock_get_valid_normal_user, client, common_user, user_token
):
    """일반 유저 회원 탈퇴 성공 테스트 (get_valid_normal_user 사용)"""
    user_info = UserInfo.objects.create(
        common_user=common_user, name="일반유저"
    )
    mock_get_valid_normal_user.return_value = user_info
    url = reverse("user:user-delete")
    response = client.delete(
        url,
        HTTP_AUTHORIZATION=f"Bearer {user_token}",
    )
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.content}")
    assert response.status_code == 200
    assert json.loads(response.content) == {
        "message": "회원 탈퇴가 완료되었습니다."
    }
    assert not CommonUser.objects.filter(pk=common_user.pk).exists()
    assert not UserInfo.objects.filter(pk=user_info.pk).exists()


@pytest.mark.django_db
@patch("utils.common.get_valid_company_user")
def test_company_user_delete_success(
    mock_get_valid_company_user, client, common_company, company_token
):
    """기업 유저 회원 탈퇴 성공 테스트 (get_valid_company_user 사용)"""
    company_info = CompanyInfo.objects.create(
        common_user=common_company,
        company_name="테스트 회사",
        establishment="2023-01-01",
        business_registration_number="123-45-67890",
    )
    mock_get_valid_company_user.return_value = company_info
    url = reverse("user:user-delete")
    response = client.delete(
        url,
        HTTP_AUTHORIZATION=f"Bearer {company_token}",
    )
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.content}")
    assert response.status_code == 200
    assert json.loads(response.content) == {
        "message": "회원 탈퇴가 완료되었습니다."
    }
    assert not CommonUser.objects.filter(pk=common_company.pk).exists()
    assert not CompanyInfo.objects.filter(pk=company_info.pk).exists()


@pytest.mark.django_db
def test_user_info_update_success(client, common_user):
    """일반 유저 정보 수정 성공 테스트"""
    user_info = UserInfo.objects.create(
        common_user=common_user, name="기존 이름", phone_number="01011112222"
    )
    url = reverse(
        "user:user-info-update", kwargs={"user_id": user_info.user_id}
    )
    token = create_access_token(common_user)
    updated_data = {
        "name": "새로운 이름",
        "phone_number": "01099998888",
        "interest": ["운동", "여행"],
    }
    response = client.patch(
        url,
        data=json.dumps(updated_data),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {token}",  # 각 요청 시 헤더 전달
    )
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.content.decode('utf-8')}")
    assert response.status_code == 200
