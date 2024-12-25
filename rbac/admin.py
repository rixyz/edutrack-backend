from django.contrib import admin

from rbac.models import Module, ModulePermission, Permission, Role, RolePermission

# Register your models here.

admin.site.register(Role)
admin.site.register(Permission)
admin.site.register(Module)
admin.site.register(RolePermission)
admin.site.register(ModulePermission)
