from datetime import datetime, timedelta

import jwt
from django.conf import settings

"""
순환참조가 발생하여 분리
"""


def create_access_token(user):
    # access_token 발급

    expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES

    expiration = datetime.now() + timedelta(minutes=expire_minutes)
    payload = {
        "sub": str(user.common_user_id),  # common_user_id
        "join_type": user.join_type,
        "is_active": user.is_active,
        "exp": expiration,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user):
    # refresh_token 발급
    expire_days = settings.REFRESH_TOKEN_EXPIRE_DAYS
    expiration = datetime.now() + timedelta(days=expire_days)
    payload = {
        "sub": str(user.common_user_id),
        "join_type": user.join_type,
        "is_active": user.is_active,
        "exp": expiration,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
