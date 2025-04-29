from typing import Any, Dict

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model


from user.redis import r
from user.views.views_token import create_access_token

User = get_user_model()

class TokenRefreshService:
    def __init__(self, refresh_token: str):
        self.refresh_token = refresh_token
        self.secret_key = settings.JWT_SECRET_KEY
        self.algorithm = settings.JWT_ALGORITHM

    def refresh(self) -> Dict[str, Any]:
        """
        Refresh Token을 검증하고 새로운 Access Token발급
        """
        try:
            # Refresh Token 검증
            try:
                payload = jwt.decode(
                    self.refresh_token,
                    self.secret_key,
                    algorithms=[self.algorithm],
                )
                user_id = payload["sub"]
                # 블랙리스트 체크
                if r.get(f"blacklist:refresh:{self.refresh_token}"):
                    return {
                        "success": False,
                        "message": "Refresh token is blacklisted. Please log in again.",
                        "status_code": 401,
                    }

                try:
                    user = User.objects.get(common_user_id=user_id)
                except User.DoesNotExist:
                    return {
                        "success": False,
                        "message": "User not found.",
                        "status_code": 404,
                    }

                # is_active = False일때
                if not user.is_active:
                    return {
                        "success": False,
                        "message": "Inactive user. Please contact support.",
                        "status_code": 403,
                    }
            except jwt.ExpiredSignatureError:
                return {
                    "success": False,
                    "message": "Refresh token has expired.",
                    "status_code": 401,
                }
            except jwt.InvalidTokenError:
                return {
                    "success": False,
                    "message": "Invalid refresh token.",
                    "status_code": 400,
                }
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Error decoding refresh token: {str(e)}",
                    "status_code": 400,
                }
                # 새로운 Access Token 발급
            new_access_token = create_access_token(user)

            return {
                "success": True,
                "access_token": new_access_token,
                "message": "Access token refreshed successfully.",
                "status_code": 200,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Server error during refresh: {str(e)}",
                "status_code": 500,
            }