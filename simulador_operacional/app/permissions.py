from rest_framework.permissions import SAFE_METHODS, BasePermission


class ProfessorWritePermission(BasePermission):
    """RN-01/RF.01: a API de administração não substitui o painel do CEO."""

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated
            and (request.method in SAFE_METHODS or request.user.is_staff)
        )
