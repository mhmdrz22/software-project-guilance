from rest_framework.permissions import BasePermission

class IsStaffUser(BasePermission):
    """
    Allows access only to users who are is_staff or is_superuser.
    """
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_staff or user.is_superuser))
