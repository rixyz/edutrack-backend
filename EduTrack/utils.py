import jwt
from django.core.exceptions import PermissionDenied

from EduTrack import settings


def get_user_id(token: str) -> str:
    """
    Decode JWT token and retrieve user.

    Args:
        token (str): JWT authentication token.

    Returns:
        user_id: Authenticated user id.

    Raises:
        PermissionDenied: If token decoding or user retrieval fails.
    """
    try:
        payload = jwt.decode(jwt=token, key=settings.SECRET_KEY, algorithms=["HS256"])
        return payload["user_id"]
    except Exception as e:
        raise PermissionDenied(f"An error occurred while authenticating the user. {e}")
