from django.core.management.base import BaseCommand
from django.db import transaction

from EduTrack.permissions import Modules, Permissions
from rbac.models import Module, ModulePermission, Permission


class Command(BaseCommand):
    help = "Generate permissions and modules based on predefined classes"

    def handle(self, *args, **options):
        module_mapping = {
            "User Management": Modules.USER_MANAGEMENT,
            "Assignment": Modules.ASSIGNMENT,
            "Course": Modules.COURSE,
        }

        permission_mapping = {
            Modules.USER_MANAGEMENT: [
                ("Create User", Permissions.CREATE_USER),
                ("Update User", Permissions.UPDATE_USER),
                ("Delete User", Permissions.DELETE_USER),
            ],
            Modules.ASSIGNMENT: [
                ("Create Assignment", Permissions.CREATE_ASSIGNMENT),
                ("Read Assignment", Permissions.READ_ASSIGNMENT),
                ("Update Assignment", Permissions.UPDATE_ASSIGNMENT),
                ("Delete Assignment", Permissions.DELETE_ASSIGNMENT),
            ],
            Modules.COURSE: [
                ("Create Course", Permissions.CREATE_COURSE),
                ("Read Course", Permissions.READ_COURSE),
                ("Update Course", Permissions.UPDATE_COURSE),
                ("Delete Course", Permissions.DELETE_COURSE),
            ],
        }

        with transaction.atomic():
            created_modules = {}
            for module_name, module_value in module_mapping.items():
                module, created = Module.objects.get_or_create(
                    name=module_name, defaults={"description": f"{module_name} module"}
                )
                created_modules[module_value] = module
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f"Created module: {module_name}")
                    )

            for module_value, permissions in permission_mapping.items():
                module = created_modules[module_value]

                for perm_name, perm_codename in permissions:
                    permission, perm_created = Permission.objects.get_or_create(
                        codename=perm_codename, defaults={"name": perm_name}
                    )

                    module_perm, mp_created = ModulePermission.objects.get_or_create(
                        module=module, permission=permission
                    )

                    if perm_created:
                        self.stdout.write(
                            self.style.SUCCESS(f"Created permission: {perm_name}")
                        )
                    if mp_created:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Created module permission: {module.name} - {perm_name}"
                            )
                        )

            self.stdout.write(
                self.style.SUCCESS("Successfully generated permissions and modules")
            )
