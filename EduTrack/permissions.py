from rest_framework.permissions import BasePermission


class Modules:
    USER_MANAGEMENT = "USER_MANAGEMENT"
    ASSIGNMENT = "ASSIGNMENT"
    COURSE = "COURSE"


class Permissions:
    # USER
    CREATE_USER = "CREATE_USER"
    UPDATE_USER = "UPDATE_USER"
    DELETE_USER = "DELETE_USER"

    # ASSIGNMENT
    CREATE_ASSIGNMENT = "CREATE_ASSIGNMENT"
    READ_ASSIGNMENT = "READ_ASSIGNMENT"
    UPDATE_ASSIGNMENT = "UPDATE_ASSIGNMENT"
    DELETE_ASSIGNMENT = "DELETE_ASSIGNMENT"

    # COURSE
    CREATE_COURSE = "CREATE_COURSE"
    READ_COURSE = "READ_COURSE"
    UPDATE_COURSE = "UPDATE_COURSE"
    DELETE_COURSE = "DELETE_COURSE"


class ModulePermission:
    USERMANAGEMENT_CREATE = Permissions.CREATE_USER
    USERMANAGEMENT_UPDATE = Permissions.UPDATE_USER
    USERMANAGEMENT_DELETE = Permissions.DELETE_USER

    ASSIGNMENT_CREATE = Permissions.CREATE_ASSIGNMENT
    ASSIGNMENT_VIEW = Permissions.READ_ASSIGNMENT
    ASSIGNMENT_UPDATE = Permissions.UPDATE_ASSIGNMENT
    ASSIGNMENT_DELETE = Permissions.DELETE_ASSIGNMENT

    COURSE_CREATE = Permissions.CREATE_COURSE
    COURSE_VIEW = Permissions.READ_COURSE
    COURSE_UPDATE = Permissions.UPDATE_COURSE
    COURSE_DELETE = Permissions.DELETE_COURSE


class CheckPermission(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return False

        if not hasattr(view, "required_permission"):
            return True

        user_role = request.user.role
        if not user_role:
            return False

        required_permissions = getattr(view, "required_permission", [])

        return all(
            permission in request.permissions for permission in required_permissions
        )
