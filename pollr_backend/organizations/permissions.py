from rest_framework import permissions


class IsOrganizationOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to only allow organization owners or admins to edit.
    """
    
    def has_object_permission(self, request, view, obj):
        # Super admins can do anything
        if request.user.is_super_admin():
            return True
        
        # Organization owner has full access
        if obj.owner == request.user:
            return True
        
        # Check if user is an admin member
        return obj.is_admin(request.user)


class IsOrganizationMember(permissions.BasePermission):
    """
    Permission to only allow organization members to access.
    """
    
    def has_object_permission(self, request, view, obj):
        # Super admins can view
        if request.user.is_super_admin():
            return True
        
        # Owner has access
        if obj.owner == request.user:
            return True
        
        # Check if user is an approved member
        return obj.is_member(request.user)


class CanManageMembers(permissions.BasePermission):
    """
    Permission to manage organization members.
    Only owners and admins can manage members.
    """
    
    def has_permission(self, request, view):
        # Must be authenticated
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # obj is OrganizationMember instance
        organization = obj.organization
        
        # Super admins can manage
        if request.user.is_super_admin():
            return True
        
        # Organization owner can manage
        if organization.owner == request.user:
            return True
        
        # Organization admins can manage
        return organization.is_admin(request.user)