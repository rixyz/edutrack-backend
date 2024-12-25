from rest_framework import serializers

from rbac.models import Permission, Role, RolePermission


class UserRoleSerializer(serializers.Serializer):
    """Serializer for assigning role to a user"""

    id = serializers.IntegerField(read_only=True)
    role = serializers.PrimaryKeyRelatedField(queryset=Role.objects.all())

    def update(self, instance, validated_data):
        role = validated_data.get("role")
        if role:
            instance.role = role
            instance.save()
        return instance


class RolePermissionSerializer(serializers.Serializer):
    """Serializer for assigning permissions to a role"""

    role = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(), required=True
    )
    permissions = serializers.ListField(
        child=serializers.PrimaryKeyRelatedField(queryset=Permission.objects.all()),
        required=True,
    )

    class Meta:
        fields = ["role", "permissions"]

    def create(self, validated_data):
        role = validated_data["role"]
        new_permissions = set(validated_data["permissions"])

        existing_permissions = set(
            RolePermission.objects.filter(role=role).values_list(
                "permission", flat=True
            )
        )

        add_permissions = new_permissions - existing_permissions
        remove_permissions = existing_permissions - new_permissions

        if remove_permissions:
            RolePermission.objects.filter(
                role=role, permission__in=remove_permissions
            ).delete()

        if add_permissions:
            role_permissions = [
                RolePermission(role=role, permission=permission)
                for permission in add_permissions
            ]
            RolePermission.objects.bulk_create(role_permissions)

        return {
            "role": role,
            "added_permissions": list(add_permissions),
            "removed_permissions": list(remove_permissions),
        }
