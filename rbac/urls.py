from django.urls import path

from rbac.views import AssignRolePermissionView, AssignUserRoleView

app_name = "rbac"

urlpatterns = [
    path(
        "roles/permissions/",
        AssignRolePermissionView.as_view(),
        name="assign-role-permissions",
    ),
    path("users/role/", AssignUserRoleView.as_view(), name="assign-user-role"),
]
