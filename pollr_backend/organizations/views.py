from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from drf_spectacular.utils import extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend

from .models import Organization, OrganizationMember, MembershipStatus, MemberRole
from .serializers import (
    OrganizationSerializer, OrganizationDetailSerializer,
    OrganizationMemberSerializer, MembershipRequestSerializer,
    MembershipJoinSerializer, MembershipActionSerializer,
    MemberRoleUpdateSerializer, OrganizationStatisticsSerializer
)
from .permissions import (
    IsOrganizationOwnerOrAdmin, IsOrganizationMember, CanManageMembers
)


@extend_schema_view(
    list=extend_schema(description='List all organizations user has access to'),
    retrieve=extend_schema(description='Retrieve organization details'),
    create=extend_schema(description='Create a new organization'),
    update=extend_schema(description='Update organization'),
    partial_update=extend_schema(description='Partially update organization'),
    destroy=extend_schema(description='Delete organization'),
)
class OrganizationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing organizations.
    
    Users can create organizations and become owners.
    Only owners and admins can modify organizations.
    """
    serializer_class = OrganizationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name']
    lookup_field = 'slug'
    
    def get_queryset(self):
        """
        Return organizations based on user permissions.
        Super admins see all, others see their organizations.
        """
        user = self.request.user
        
        if self.action == 'list':
            if user.is_super_admin():
                return Organization.objects.all()
            return Organization.objects.filter(
                Q(owner=user) |
                Q(members__user=user, members__membership_status=MembershipStatus.APPROVED)
            ).distinct()
    
        # For detail view, return all and let permissions handle access
        return Organization.objects.all()
    
    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == 'retrieve':
            return OrganizationDetailSerializer
        return OrganizationSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['update', 'partial_update', 'destroy', 'suspend', 'activate']:
            return [IsAuthenticated(), IsOrganizationOwnerOrAdmin()]
        return [IsAuthenticated()]
    
    @extend_schema(
        description='Get organizations owned by current user',
        responses={200: OrganizationSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def my_organizations(self, request):
        """Get organizations owned by current user."""
        orgs = Organization.objects.filter(owner=request.user)
        serializer = self.get_serializer(orgs, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description='Get organizations where user is a member',
        responses={200: OrganizationSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def joined_organizations(self, request):
        """Get organizations where user is an approved member."""
        orgs = Organization.objects.filter(
            members__user=request.user,
            members__membership_status=MembershipStatus.APPROVED
        )
        serializer = self.get_serializer(orgs, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description='Invite a user to join the organization',
        request=MembershipRequestSerializer,
        responses={201: OrganizationMemberSerializer}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsOrganizationOwnerOrAdmin])
    def invite_member(self, request, slug=None):
        """Invite a user to join the organization."""
        organization = self.get_object()
        if not organization.can_manage(request.user):
            return Response(
                {'error': 'You do not have permission to invite members.'},
                status=status.HTTP_403_FORBIDDEN
            )
    
        serializer = MembershipRequestSerializer(
            data=request.data,
            context={'organization': organization}
        )
        serializer.is_valid(raise_exception=True)
    
        member = OrganizationMember.objects.create(
            user=serializer.validated_data['user'],
            organization=organization,
            role=serializer.validated_data.get('role', MemberRole.VOTER),
            membership_status=MembershipStatus.PENDING,
            invited_by=request.user
        )
    
        return Response(
            OrganizationMemberSerializer(member).data,
            status=status.HTTP_201_CREATED
        )
    
    @extend_schema(
        description='Request to join an organization',
        request=MembershipJoinSerializer,
        responses={201: OrganizationMemberSerializer}
    )
    @action(detail=False, methods=['post'])
    def join_request(self, request):
        """Request to join an organization."""
        serializer = MembershipJoinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        organization = get_object_or_404(
            Organization,
            slug=serializer.validated_data['organization_slug']
        )
        
        # Check if user is owner
        if organization.owner == request.user:
            return Response(
                {'error': 'You are the owner of this organization.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if membership already exists
        if OrganizationMember.objects.filter(
            user=request.user,
            organization=organization
        ).exists():
            return Response(
                {'error': 'You already have a membership request or are a member.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        member = OrganizationMember.objects.create(
            user=request.user,
            organization=organization,
            role=MemberRole.VOTER,
            membership_status=MembershipStatus.PENDING
        )
        
        return Response(
            OrganizationMemberSerializer(member).data,
            status=status.HTTP_201_CREATED
        )
    
    @extend_schema(
        description='Get organization statistics',
        responses={200: OrganizationStatisticsSerializer}
    )
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsOrganizationMember])
    def statistics(self, request, slug=None):
        """Get organization statistics."""
        organization = self.get_object()
        
        members = organization.members.all()
        stats = {
            'total_members': members.count(),
            'approved_members': members.filter(membership_status=MembershipStatus.APPROVED).count(),
            'pending_members': members.filter(membership_status=MembershipStatus.PENDING).count(),
            'rejected_members': members.filter(membership_status=MembershipStatus.REJECTED).count(),
            'admin_count': members.filter(
                membership_status=MembershipStatus.APPROVED,
                role=MemberRole.ADMIN
            ).count(),
            'voter_count': members.filter(
                membership_status=MembershipStatus.APPROVED,
                role=MemberRole.VOTER
            ).count(),
            'total_elections': organization.elections.count() if hasattr(organization, 'elections') else 0,
            'active_elections': organization.elections.filter(status='ongoing').count() if hasattr(organization, 'elections') else 0,
        }
        
        return Response(stats)
    
    @extend_schema(
        description='Suspend organization (Super Admin only)',
        responses={200: OrganizationSerializer}
    )
    @action(detail=True, methods=['post'])
    def suspend(self, request, slug=None):
        """Suspend an organization."""
        organization = self.get_object()
        organization.suspend()
        serializer = self.get_serializer(organization)
        return Response(serializer.data)
    
    @extend_schema(
        description='Activate organization (Super Admin only)',
        responses={200: OrganizationSerializer}
    )
    @action(detail=True, methods=['post'])
    def activate(self, request, slug=None):
        """Activate an organization."""
        organization = self.get_object()
        organization.activate()
        serializer = self.get_serializer(organization)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(description='List organization members'),
    retrieve=extend_schema(description='Retrieve member details'),
    update=extend_schema(description='Update member'),
    partial_update=extend_schema(description='Partially update member'),
    destroy=extend_schema(description='Remove member from organization'),
)
class OrganizationMemberViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing organization members.
    
    Only organization owners and admins can manage members.
    """
    serializer_class = OrganizationMemberSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['membership_status', 'role']
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        """Return members based on organization access."""
        user = self.request.user
        
        if user.is_super_admin():
            return OrganizationMember.objects.all()
        
        # Get members of organizations user can access
        return OrganizationMember.objects.filter(
            Q(organization__owner=user) |
            Q(organization__members__user=user, 
              organization__members__membership_status=MembershipStatus.APPROVED)
        ).distinct()
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), CanManageMembers()]
        return [IsAuthenticated()]
    
    @extend_schema(
        description='Get pending membership requests',
        responses={200: OrganizationMemberSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get all pending membership requests for organizations user manages."""
        user = request.user
        
        members = OrganizationMember.objects.filter(
            organization__owner=user,
            membership_status=MembershipStatus.PENDING
        ) | OrganizationMember.objects.filter(
            organization__members__user=user,
            organization__members__role=MemberRole.ADMIN,
            organization__members__membership_status=MembershipStatus.APPROVED,
            membership_status=MembershipStatus.PENDING
        )
        
        members = members.distinct()
        serializer = self.get_serializer(members, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description='Approve or reject membership request',
        request=MembershipActionSerializer,
        responses={200: OrganizationMemberSerializer}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanManageMembers])
    def review(self, request, pk=None):
        """Approve or reject a membership request."""
        member = self.get_object()
        serializer = MembershipActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        action_type = serializer.validated_data['action']
        
        if action_type == 'approve':
            member.approve()
            message = 'Membership approved successfully.'
        else:
            member.reject()
            message = 'Membership rejected.'
        
        return Response({
            'message': message,
            'member': OrganizationMemberSerializer(member).data
        })
    
    @extend_schema(
        description='Update member role',
        request=MemberRoleUpdateSerializer,
        responses={200: OrganizationMemberSerializer}
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanManageMembers])
    def update_role(self, request, pk=None):
        """Update member's role."""
        member = self.get_object()
        
        if member.membership_status != MembershipStatus.APPROVED:
            return Response(
                {'error': 'Can only update role for approved members.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = MemberRoleUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        new_role = serializer.validated_data['role']
        
        if new_role == MemberRole.ADMIN:
            member.promote_to_admin()
            message = 'Member promoted to admin.'
        else:
            member.demote_to_voter()
            message = 'Member demoted to voter.'
        
        return Response({
            'message': message,
            'member': OrganizationMemberSerializer(member).data
        })
    
    @extend_schema(
        description='Leave organization',
        responses={204: None}
    )
    @action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        """Leave an organization."""
        member = self.get_object()
        
        # Can only leave if you're the member
        if member.user != request.user:
            return Response(
                {'error': 'You can only leave organizations you are a member of.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Cannot leave if you're the owner
        if member.organization.owner == request.user:
            return Response(
                {'error': 'Organization owners cannot leave. Transfer ownership or delete the organization.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        member.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)