from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    ChangePasswordSerializer, UserAdminSerializer
)
from .permissions import IsOwnerOrAdmin, IsSuperAdmin

User = get_user_model()


@extend_schema_view(
    list=extend_schema(description='List all users (Admin only)'),
    retrieve=extend_schema(description='Retrieve a specific user'),
    create=extend_schema(description='Register a new user'),
    update=extend_schema(description='Update user details'),
    partial_update=extend_schema(description='Partially update user details'),
    destroy=extend_schema(description='Delete a user (Admin only)'),
)
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management.
    
    Provides CRUD operations for users with appropriate permissions.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action == 'create':
            return [AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrAdmin()]
        elif self.action in ['list', 'suspend_user', 'activate_user']:
            return [IsAuthenticated(), IsSuperAdmin()]
        return [IsAuthenticated()]
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        elif self.action == 'change_password':
            return ChangePasswordSerializer
        elif self.action in ['suspend_user', 'activate_user', 'list']:
            return UserAdminSerializer
        return UserSerializer
    
    def get_queryset(self):
        """Filter queryset based on user permissions."""
        user = self.request.user
        if user.is_authenticated and user.is_super_admin():
            return User.objects.all()
        return User.objects.filter(id=user.id)
    
    @extend_schema(
        description='Get current authenticated user profile',
        responses={200: UserSerializer}
    )
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's profile."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @extend_schema(
        description='Change current user password',
        request=ChangePasswordSerializer,
        responses={200: {'description': 'Password changed successfully'}}
    )
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Change the current user's password."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'Password changed successfully.'
        }, status=status.HTTP_200_OK)
    
    @extend_schema(
        description='Suspend a user account (Super Admin only)',
        responses={200: UserAdminSerializer}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSuperAdmin])
    def suspend(self, request, pk=None):
        """Suspend a user account."""
        user = self.get_object()
        if user.is_super_admin():
            return Response({
                'error': 'Cannot suspend a super admin.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user.suspend()
        serializer = self.get_serializer(user)
        return Response(serializer.data)
    
    @extend_schema(
        description='Activate a user account (Super Admin only)',
        responses={200: UserAdminSerializer}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsSuperAdmin])
    def activate(self, request, pk=None):
        """Activate a user account."""
        user = self.get_object()
        user.activate()
        serializer = self.get_serializer(user)
        return Response(serializer.data)
    
    @extend_schema(
        description='Get user statistics (Super Admin only)',
        responses={200: {
            'type': 'object',
            'properties': {
                'total_users': {'type': 'integer'},
                'active_users': {'type': 'integer'},
                'suspended_users': {'type': 'integer'},
                'super_admins': {'type': 'integer'},
                'org_admins': {'type': 'integer'},
                'regular_users': {'type': 'integer'},
            }
        }}
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsSuperAdmin])
    def statistics(self, request):
        """Get user statistics."""
        from .models import UserStatus, UserRole
        
        stats = {
            'total_users': User.objects.count(),
            'active_users': User.objects.filter(status=UserStatus.ACTIVE).count(),
            'suspended_users': User.objects.filter(status=UserStatus.SUSPENDED).count(),
            'super_admins': User.objects.filter(role=UserRole.SUPER_ADMIN).count(),
            'org_admins': User.objects.filter(role=UserRole.ORG_ADMIN).count(),
            'regular_users': User.objects.filter(role=UserRole.USER).count(),
        }
        return Response(stats)