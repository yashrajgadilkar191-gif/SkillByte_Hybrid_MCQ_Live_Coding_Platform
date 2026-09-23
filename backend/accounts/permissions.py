"""
Reusable permission classes for SKILLBYTE Role-Based Access Control (RBAC).
"""

from rest_framework.permissions import BasePermission
from .models import Role


class IsStudent(BasePermission):
    """
    Allows access only to authenticated users with the STUDENT role.
    Unauthenticated requests receive 401; wrong role receives 403.
    """
    message = "Access restricted to registered students only."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return hasattr(request.user, 'profile') and request.user.profile.role == Role.STUDENT


class IsAdmin(BasePermission):
    """
    Allows access only to authenticated users with the ADMIN role or superuser status.
    Unauthenticated requests receive 401; non-admin users receive 403.
    """
    message = "Administrator privileges required to access this resource."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser or request.user.is_staff:
            return True
        return hasattr(request.user, 'profile') and request.user.profile.role == Role.ADMIN


class IsGuestOrReadOnly(BasePermission):
    """
    Allows guest access for open exploration / public assessments.
    """
    def has_permission(self, request, view):
        return True

