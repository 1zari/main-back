from unittest.mock import patch

import pytest
from django.test import Client
from django.test.utils import override_settings
from django.urls import reverse

from user.redis import r


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def valid_verification_code_data():
    return {"phone_number": "01012345678", "code": "123456"}


@pytest.fixture
def invalid_verification_code_data():
    return {"phone_number": "01012345678", "code": "wrong_code"}


@pytest.mark.django_db
@override_settings(
    aligo_api_key="test_api_key",
    aligo_user_id="test_user_id",
    aligo_sender="01000000000",
)
def test_send_verification_code(client):
    """인증번호 전송 테스트"""

    url = reverse("user:send-verification-code")
    data = {"phone_number": "01012345678"}

    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "result_code": 1,
            "message": "인증번호 전송 성공",
        }

        with patch("user.redis.r") as mock_r:
            mock_redis_instance = mock_r.return_value
            mock_redis_instance.setex.return_value = (
                True  # Redis에 값 저장된 것으로 설정
            )

            response = client.post(url, data, content_type="application/json")

            assert response.status_code == 200
            assert response.json()["message"] == "인증번호 전송 성공"


@pytest.mark.django_db
def test_verify_code_success(client, valid_verification_code_data):
    """인증번호 검증 성공 테스트"""

    url = reverse("user:verify-code")

    # Redis get 모킹
    with patch.object(r, "get") as mock_get:
        mock_get.return_value = "123456"  # Redis에서 저장된 인증번호 반환

        response = client.post(
            url, valid_verification_code_data, content_type="application/json"
        )

        assert response.status_code == 200
        assert response.json()["message"] == "인증 성공!"


@pytest.mark.django_db
def test_verify_code_failure(client, invalid_verification_code_data):
    """인증번호 검증 실패 테스트"""

    url = reverse("user:verify-code")

    # Redis get 모킹
    with patch.object(r, "get") as mock_get:
        mock_get.return_value = "123456"  # Redis에 저장된 인증번호

        response = client.post(
            url, invalid_verification_code_data, content_type="application/json"
        )

        assert response.status_code == 400
        assert response.json()["message"] == "인증 코드가 일치하지 않습니다."


@pytest.mark.django_db
@patch("requests.post")
def test_verify_business_registration_success(mock_post, client, settings):
    """사업자등록번호 검증 성공 테스트"""
    url = reverse("user:verify-business")
    data = {"b_no": "1234567890", "p_nm": "홍길동", "start_dt": "20200101"}

    # mock response 설정
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "data": [
            {
                "b_no": "1234567890",
                "valid": "01",
                "valid_msg": "정상 등록된 사업자입니다.",
            }
        ]
    }

    # API KEY 설정
    settings.KOREA_TAX_API_KEY = "test_api_key"

    response = client.post(url, data=data, content_type="application/json")

    assert response.status_code == 200
    assert response.json()["valid"] is True
    assert "사업자 정보가 일치합니다." in response.json()["message"]


@pytest.mark.django_db
@patch("requests.post")
def test_verify_business_registration_fail(mock_post, client, settings):
    """사업자등록번호 검증 실패 테스트"""
    url = reverse("user:verify-business")
    data = {"b_no": "0000000000", "p_nm": "홍길동", "start_dt": "20200101"}

    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "data": [
            {
                "b_no": "0000000000",
                "valid": "02",
                "valid_msg": "등록되지 않은 사업자입니다.",
            }
        ]
    }

    settings.KOREA_TAX_API_KEY = "test_api_key"

    response = client.post(url, data=data, content_type="application/json")

    assert response.status_code == 200
    assert response.json()["valid"] is False
    assert "등록되지 않은 사업자입니다." in response.json()["message"]
