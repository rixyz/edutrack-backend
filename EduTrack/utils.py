from typing import Any

import jwt
from django.core.exceptions import PermissionDenied
from rest_framework import exceptions

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


def get_or_not_found(qs: Any, **kwargs: Any) -> Any:
    """
    Retrieve a single instance from a queryset or raise a NotFound exception if not found.

    Args:
        qs: Queryset from which to retrieve the instance.
        **kwargs: Lookup parameters to filter the queryset.

    Returns:
        An instance of the model matching the provided parameters.

    Raises:
        NotFound: If no instance matching the parameters is found.
    """
    try:
        return qs.get(**kwargs)
    except qs.model.DoesNotExist:
        raise exceptions.NotFound(f"{qs.model.__name__} not found.")
