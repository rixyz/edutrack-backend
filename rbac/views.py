from drf_yasg.utils import swagger_auto_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from EduTrack.utils import get_or_not_found
from rbac.serializers import RolePermissionSerializer, UserRoleSerializer
from users.models import User


class AssignRolePermissionView(APIView):
    """
    API endpoint to assign multiple permissions to a role.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = RolePermissionSerializer

    @swagger_auto_schema(
        tags=["Permissions"],
        operation_description="Assign multiple permissions to a specific role",
        operation_summary="Assign Permissions to Role",
        request_body=RolePermissionSerializer,
        responses={
            200: "Permissions successfully assigned",
            400: "Bad Request - Invalid role or permissions",
            401: "Unauthorized",
        },
    )
    def post(self, request):
        """
        Assign permissions to a role.
        """
        serializer = self.serializer_class(data=request.data)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {
                "message": "Permissions assigned successfully",
                "status": "permissions_assigned",
            },
            status=status.HTTP_200_OK,
        )


class AssignUserRoleView(APIView):
    """
    API endpoint to assign a role to a user.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserRoleSerializer

    @swagger_auto_schema(
        tags=["Permissions"],
        operation_description="Assign a role to a specific user",
        operation_summary="Assign Role to User",
        request_body=UserRoleSerializer,
        responses={
            200: "Role successfully assigned",
            400: "Bad Request - Invalid user or role",
            401: "Unauthorized",
        },
    )
    def patch(self, request):
        """
        Assign a role to a user.
        """
        user_id = request.data.get("id")
        user = get_or_not_found(User.objects.all(), pk=user_id)

        serializer = self.serializer_class(user, data=request.data, partial=True)

        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "message": "Role assigned successfully",
                "status": "role_assigned",
                "user_id": user.id,
            },
            status=status.HTTP_200_OK,
        )
