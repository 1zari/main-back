import json
from unittest.mock import patch

import pytest
from django.test import Client
from django.urls import reverse

from user.models import CommonUser, UserInfo


@pytest.mark.django_db
@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
@pytest.fixture
def kakao_login_url():
    return reverse("user:kakao-login")


@pytest.mark.django_db
@pytest.fixture
def naver_login_url():
    return reverse("user:naver-login")


@pytest.mark.django_db
@pytest.fixture
def mock_kakao_access_token():
    return "test_kakao_access_token"


@pytest.mark.django_db
@pytest.fixture
def mock_kakao_user_data():
    return {
        "id": 12345,
        "kakao_account": {
            "email": "test@example.com",
        },
    }


@pytest.mark.django_db
@pytest.fixture
def mock_naver_access_token():
    return "test_naver_access_token"


@pytest.mark.django_db
@pytest.fixture
def mock_naver_user_data():
    return {
        "response": {
            "email": "test@example.com",
        },
    }


# 1. 신규 사용자 로그인 (카카오)
@pytest.mark.django_db
@patch("user.views.views_oauth.KakaoLoginView.get_kakao_user_info")
def test_kakao_login_new_user(
    mock_get_kakao_user_info,
    client,
    kakao_login_url,
    mock_kakao_access_token,
    mock_kakao_user_data,
):
    mock_get_kakao_user_info.return_value = mock_kakao_user_data

    response = client.get(f"{kakao_login_url}?access_token={mock_kakao_access_token}")
    assert response.status_code == 202
    assert json.loads(response.content) == {
        "message": "Additional information required.",
        "email": "test@example.com",
    }
    assert CommonUser.objects.filter(email="test@example.com", join_type="normal").exists()


# 2. 신규 사용자 로그인 (네이버)
@pytest.mark.django_db
@patch("user.views.views_oauth.NaverLoginView.get_naver_user_info")
def test_naver_login_new_user(
    mock_get_naver_user_info,
    client,
    naver_login_url,
    mock_naver_access_token,
    mock_naver_user_data,
):
    mock_get_naver_user_info.return_value = mock_naver_user_data

    response = client.get(f"{naver_login_url}?access_token={mock_naver_access_token}")
    assert response.status_code == 202
    assert json.loads(response.content) == {
        "message": "Additional information required.",
        "email": "test@example.com",
    }
    assert CommonUser.objects.filter(email="test@example.com", join_type="normal").exists()


# 3. 기존 사용자 로그인 (카카오)
@pytest.mark.django_db
@patch("user.views.views_oauth.KakaoLoginView.get_kakao_user_info")
def test_kakao_login_existing_user(
    mock_get_kakao_user_info,
    client,
    kakao_login_url,
    mock_kakao_access_token,
    mock_kakao_user_data,
):
    # 기존 사용자 생성
    common_user = CommonUser.objects.create(email="test@example.com", join_type="user", password="test_password")
    # UserInfo 객체 생성: 추가 정보 입력이 완료된 상태로 설정
    UserInfo.objects.create(
        common_user=common_user,
        name="Test User",
        phone_number="010-1234-5678",
        gender="Female",
        birthday="1990-01-01",
        interest=["Technology", "Science"],
        purpose_subscription=["Job Search"],
        route=["Social Media"],
    )

    mock_get_kakao_user_info.return_value = mock_kakao_user_data

    response = client.get(f"{kakao_login_url}?access_token={mock_kakao_access_token}")
    assert response.status_code == 200
    response_data = json.loads(response.content)
    assert "access_token" in response_data
    assert "refresh_token" in response_data
    assert response_data["message"] == "Login successful."


# 4. 기존 사용자 로그인 (네이버)
@pytest.mark.django_db
@patch("user.views.views_oauth.NaverLoginView.get_naver_user_info")
def test_naver_login_existing_user(
    mock_get_naver_user_info,
    client,
    naver_login_url,
    mock_naver_access_token,
    mock_naver_user_data,
):
    # 기존 사용자 생성
    common_user = CommonUser.objects.create(email="test@example.com", join_type="user", password="test_password")
    # UserInfo 객체 생성: 추가 정보 입력이 완료된 상태로 설정
    UserInfo.objects.create(
        common_user=common_user,
        name="Test User",
        phone_number="010-1234-5678",
        gender="Female",
        birthday="1990-01-01",
        interest=["Technology", "Science"],
        purpose_subscription=["Job Search"],
        route=["Social Media"],
    )

    mock_get_naver_user_info.return_value = mock_naver_user_data

    response = client.get(f"{naver_login_url}?access_token={mock_naver_access_token}")
    assert response.status_code == 200
    response_data = json.loads(response.content)
    assert "access_token" in response_data
    assert "refresh_token" in response_data
    assert response_data["message"] == "Login successful."
