from datetime import datetime

import jwt
import pytest
from django.conf import settings
from django.test.client import Client

from user.models import CommonUser
from user.services.token import create_access_token, create_refresh_token


@pytest.fixture
def common_user_data():
    return {
        "email": "testuser@example.com",
        "password": "testpassword123",
        "join_type": "normal",
        "is_active": True,
    }


@pytest.fixture
def create_common_user(common_user_data):
    user = CommonUser.objects.create_user(**common_user_data)
    assert user.check_password(
        common_user_data["password"]
    ), "Password was not hashed correctly"
    return user


@pytest.mark.django_db
def test_create_access_token(common_user_data):

    user = CommonUser.objects.create_user(**common_user_data)

    access_token = create_access_token(user)

    assert access_token is not None

    try:
        decoded_token = jwt.decode(
            access_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        assert decoded_token["sub"] == str(user.common_user_id)
        assert decoded_token["join_type"] == user.join_type
        assert decoded_token["is_active"] == user.is_active
        assert "exp" in decoded_token
        assert decoded_token["exp"] > datetime.now().timestamp()

    except jwt.ExpiredSignatureError:
        pytest.fail("Token has expired")
    except jwt.InvalidTokenError:
        pytest.fail("Token is invalid")


@pytest.mark.django_db
def test_create_refresh_token(common_user_data):

    user = CommonUser.objects.create_user(**common_user_data)

    refresh_token = create_refresh_token(user)

    assert refresh_token is not None

    try:
        decoded_token = jwt.decode(
            refresh_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        assert decoded_token["sub"] == str(user.common_user_id)  #
        assert decoded_token["join_type"] == user.join_type
        assert decoded_token["is_active"] == user.is_active
        assert "exp" in decoded_token
        assert decoded_token["exp"] > datetime.now().timestamp()

    except jwt.ExpiredSignatureError:
        pytest.fail("Token has expired")
    except jwt.InvalidTokenError:
        pytest.fail("Token is invalid")


@pytest.mark.django_db
def test_token_refresh_view(create_common_user):

    user = create_common_user

    refresh_token = create_refresh_token(user)

    client = Client()

    response = client.post(
        "/api/user/token/refresh/",
        {"refresh_token": refresh_token},
        content_type="application/json",
    )

    assert response.status_code == 200

    new_access_token = response.json().get("access_token")
    assert new_access_token is not None

    try:
        decoded_token = jwt.decode(
            new_access_token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        assert decoded_token["sub"] == str(user.common_user_id)  #
        assert decoded_token["join_type"] == user.join_type
        assert decoded_token["is_active"] == user.is_active
        assert "exp" in decoded_token
        assert decoded_token["exp"] > datetime.now().timestamp()  #

    except jwt.ExpiredSignatureError:
        pytest.fail("Token has expired")
    except jwt.InvalidTokenError:
        pytest.fail("Token is invalid")
