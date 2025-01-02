from django.contrib import admin
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget
from unfold.admin import TabularInline

from rbac.models import Permission, Role, RolePermission
from utils.admin_import_export import ImportExportBase


class RolePermissionResource(resources.ModelResource):
    """Resource for RolePermission import/export with ID-based permission matching."""

    role = fields.Field(
        column_name="role", attribute="role", widget=ForeignKeyWidget(Role, "name")
    )

    permission = fields.Field(
        column_name="permission_codename",
        attribute="permission",
        widget=ForeignKeyWidget(Permission, "codename"),
    )

    class Meta:
        model = RolePermission
        fields = ("role", "permission")
        import_id_fields = ["role", "permission"]


class RolePermissionInline(TabularInline):
    """Inline admin for managing permissions in a role."""

    model = RolePermission
    extra = 1


@admin.register(Role)
class RoleAdmin(ImportExportBase):
    inlines = [RolePermissionInline]


@admin.register(RolePermission)
class RolePermissionAdmin(ImportExportBase):
    resource_class = RolePermissionResource
    list_display = ["role", "permission"]
    list_filter = ["role"]
    search_fields = ["role__name", "permission__name"]
