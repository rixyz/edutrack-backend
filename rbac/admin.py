from django.contrib import admin
from unfold.admin import TabularInline

from rbac.models import Role, RolePermission
from utils.admin_import_export import ImportExportBase


class RolePermissionInline(TabularInline):
    """Inline admin for managing permissions in a role."""

    model = RolePermission
    extra = 1


@admin.register(Role)
class RoleAdmin(ImportExportBase):
    inlines = [RolePermissionInline]
