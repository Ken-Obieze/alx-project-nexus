from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to only allow owners of an object or admins to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Super admins can do anything
        if request.user.is_super_admin():
            return True
        
        # Users can only edit their own profile
        return obj == request.user


class IsSuperAdmin(permissions.BasePermission):
    """
    Permission to only allow super admins.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_super_admin()


class IsOrgAdminOrAbove(permissions.BasePermission):
    """
    Permission to allow org admins and super admins.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and (
            request.user.is_super_admin() or request.user.is_org_admin()
        )