from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q
from drf_spectacular.utils import extend_schema, extend_schema_view
from django_filters.rest_framework import DjangoFilterBackend

from .models import Election, Position, Candidate
from .serializers import (
    ElectionSerializer, ElectionDetailSerializer, ElectionCreateSerializer,
    PositionSerializer, PositionDetailSerializer,
    CandidateSerializer, CandidateCreateSerializer
)
from organizations.permissions import IsOrganizationOwnerOrAdmin


@extend_schema_view(
    list=extend_schema(description='List elections'),
    retrieve=extend_schema(description='Retrieve election details'),
    create=extend_schema(description='Create a new election'),
    update=extend_schema(description='Update election'),
    partial_update=extend_schema(description='Partially update election'),
    destroy=extend_schema(description='Delete election'),
)
class ElectionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing elections.
    
    Organization owners and admins can create and manage elections.
    Members can view and vote in elections.
    """
    serializer_class = ElectionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'organization']
    search_fields = ['title', 'description']
    ordering_fields = ['start_at', 'created_at']
    
    def get_queryset(self):
        """Return elections based on user access."""
        user = self.request.user
        
        if user.is_super_admin():
            return Election.objects.all()
        
        # Get elections from organizations user has access to
        return Election.objects.filter(
            Q(organization__owner=user) |
            Q(organization__members__user=user, 
              organization__members__membership_status='approved')
        ).distinct()
    
    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == 'create':
            return ElectionCreateSerializer
        elif self.action == 'retrieve':
            return ElectionDetailSerializer
        return ElectionSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'start', 'end']:
            return [IsAuthenticated(), IsOrganizationOwnerOrAdmin()]
        return [IsAuthenticated()]
    
    @extend_schema(
        description='Get elections for a specific organization',
        responses={200: ElectionSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def by_organization(self, request):
        """Get elections for a specific organization."""
        org_slug = request.query_params.get('organization_slug')
        if not org_slug:
            return Response(
                {'error': 'organization_slug parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        elections = self.get_queryset().filter(organization__slug=org_slug)
        serializer = self.get_serializer(elections, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description='Get active elections',
        responses={200: ElectionSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get all active (ongoing) elections."""
        elections = self.get_queryset().filter(status='ongoing')
        serializer = self.get_serializer(elections, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description='Get upcoming elections',
        responses={200: ElectionSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get all upcoming (scheduled) elections."""
        elections = self.get_queryset().filter(status='scheduled')
        serializer = self.get_serializer(elections, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description='Get completed elections',
        responses={200: ElectionSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def completed(self, request):
        """Get all completed elections."""
        elections = self.get_queryset().filter(status='completed')
        serializer = self.get_serializer(elections, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description='Manually start an election',
        responses={200: ElectionSerializer}
    )
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Manually start an election."""
        election = self.get_object()
        
        if election.status != 'scheduled':
            return Response(
                {'error': 'Only scheduled elections can be started.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        election.start()
        serializer = self.get_serializer(election)
        return Response(serializer.data)
    
    @extend_schema(
        description='Manually end an election',
        responses={200: ElectionSerializer}
    )
    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        """Manually end an election."""
        election = self.get_object()
        
        if election.status == 'completed':
            return Response(
                {'error': 'Election is already completed.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        election.end()
        serializer = self.get_serializer(election)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(description='List positions'),
    retrieve=extend_schema(description='Retrieve position details'),
    create=extend_schema(description='Create a new position'),
    update=extend_schema(description='Update position'),
    partial_update=extend_schema(description='Partially update position'),
    destroy=extend_schema(description='Delete position'),
)
class PositionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing election positions.
    
    Organization owners and admins can manage positions.
    """
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['election']
    ordering_fields = ['order_index', 'created_at']
    
    def get_queryset(self):
        """Return positions based on user access."""
        user = self.request.user
        
        if user.is_super_admin():
            return Position.objects.all()
        
        return Position.objects.filter(
            Q(election__organization__owner=user) |
            Q(election__organization__members__user=user,
              election__organization__members__membership_status='approved')
        ).distinct()
    
    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == 'retrieve':
            return PositionDetailSerializer
        return PositionSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # Check if user can manage the election's organization
            return [IsAuthenticated(), IsOrganizationOwnerOrAdmin()]
        return [IsAuthenticated()]


@extend_schema_view(
    list=extend_schema(description='List candidates'),
    retrieve=extend_schema(description='Retrieve candidate details'),
    create=extend_schema(description='Create a new candidate'),
    update=extend_schema(description='Update candidate'),
    partial_update=extend_schema(description='Partially update candidate'),
    destroy=extend_schema(description='Delete candidate'),
)
class CandidateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing candidates.
    
    Organization owners and admins can manage candidates.
    """
    serializer_class = CandidateSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['position', 'user']
    search_fields = ['name', 'manifesto']
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        """Return candidates based on user access."""
        user = self.request.user
        
        if user.is_super_admin():
            return Candidate.objects.all()
        
        return Candidate.objects.filter(
            Q(position__election__organization__owner=user) |
            Q(position__election__organization__members__user=user,
              position__election__organization__members__membership_status='approved')
        ).distinct()
    
    def get_serializer_class(self):
        """Return appropriate serializer."""
        if self.action == 'create':
            return CandidateCreateSerializer
        return CandidateSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOrganizationOwnerOrAdmin()]
        return [IsAuthenticated()]
    
    @extend_schema(
        description='Get candidates for a specific position',
        responses={200: CandidateSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def by_position(self, request):
        """Get candidates for a specific position."""
        position_id = request.query_params.get('position_id')
        if not position_id:
            return Response(
                {'error': 'position_id parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        candidates = self.get_queryset().filter(position_id=position_id)
        serializer = self.get_serializer(candidates, many=True)
        return Response(serializer.data)