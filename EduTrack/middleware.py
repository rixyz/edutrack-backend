import logging

from django.http import HttpRequest, HttpResponse

from EduTrack.utils import get_or_not_found, get_user_id
from rbac.models import RolePermission
from users.models import User

logger = logging.getLogger(__name__)


class RolePermissionsMiddleware:
    """
    Middleware to retrieve and attach user permissions to the request object.
    """

    def __init__(self, get_response: callable):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request.permissions = []

        auth_header = request.headers.get("Authorization", "")
        if not auth_header:
            return self.get_response(request)

        try:
            token = auth_header.split()[-1]
            user_id = get_user_id(token)
            user = get_or_not_found(User.objects.all(), pk=user_id)

            if user and user.role:
                permissions = (
                    RolePermission.objects.filter(role=user.role)
                    .select_related("permission")
                    .values_list("permission__codename", flat=True)
                )
                request.permissions = list(permissions)
        except Exception as e:
            print(f"Error fetching permissions: {e}")

        response = self.get_response(request)

        return response
