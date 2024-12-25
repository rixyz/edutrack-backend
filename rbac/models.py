from django.db import models


class Module(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Permission(models.Model):
    name = models.CharField(max_length=255)
    codename = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"({self.id}) {self.name}"


class Role(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    def __str__(self):
        return f"({self.role}: {self.permission})"

    class Meta:
        unique_together = (
            "role",
            "permission",
        )


class ModulePermission(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.module}: {self.permission}"

    class Meta:
        unique_together = (
            "module",
            "permission",
        )
