from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction, models
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Vote
from .serializers import (
    VoteSerializer, CastVoteSerializer, BulkVoteSerializer,
    ElectionResultSerializer
)
from elections.models import Election
from organizations.models import OrganizationMember


@extend_schema_view(
    list=extend_schema(description='List votes (admin only)'),
    retrieve=extend_schema(description='Retrieve vote details'),
)
class VoteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing votes.
    
    Only super admins can view all votes.
    Regular users can view their own votes.
    """
    serializer_class = VoteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Return votes based on user permissions."""
        user = self.request.user
        
        if user.is_super_admin():
            return Vote.objects.all()
        
        # Regular users can only see their own votes
        return Vote.objects.filter(
            models.Q(voter__user=user) | models.Q(voter_user=user)
        )
    
    @extend_schema(
        description='Get current user votes for a specific election',
        responses={200: VoteSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def my_votes(self, request):
        """Get current user's votes for a specific election."""
        election_id = request.query_params.get('election_id')
        if not election_id:
            return Response(
                {'error': 'election_id parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        votes = Vote.get_user_votes_for_election(
            election=election_id,
            user=request.user
        )
        serializer = self.get_serializer(votes, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        description='Cast a vote',
        request=CastVoteSerializer,
        responses={201: VoteSerializer}
    )
    @action(detail=False, methods=['post'])
    def cast(self, request):
        """Cast a single vote."""
        election_id = request.data.get('election_id')
        if not election_id:
            return Response(
                {'error': 'election_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        election = get_object_or_404(Election, id=election_id)
        
        serializer = CastVoteSerializer(
            data=request.data,
            context={'election': election, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # Create the vote
        vote_data = {
            'election': election,
            'position': serializer.validated_data['position'],
            'candidate': serializer.validated_data['candidate'],
        }
        
        # Determine if voting as member or owner
        if election.organization.owner == request.user:
            vote_data['voter_user'] = request.user
        else:
            member = OrganizationMember.objects.get(
                user=request.user,
                organization=election.organization,
                membership_status='approved'
            )
            vote_data['voter'] = member
        
        vote = Vote.objects.create(**vote_data)
        
        return Response(
            VoteSerializer(vote).data,
            status=status.HTTP_201_CREATED
        )
    
    @extend_schema(
        description='Cast multiple votes at once',
        request=BulkVoteSerializer,
        responses={201: VoteSerializer(many=True)}
    )
    @action(detail=False, methods=['post'])
    def bulk_cast(self, request):
        """Cast multiple votes at once (one per position)."""
        election_id = request.data.get('election_id')
        if not election_id:
            return Response(
                {'error': 'election_id is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        election = get_object_or_404(Election, id=election_id)
        
        serializer = BulkVoteSerializer(
            data=request.data,
            context={'election': election, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        # Create all votes in a transaction
        votes_created = []
        with transaction.atomic():
            for vote_data in serializer.validated_data['validated_votes']:
                vote_create_data = {
                    'election': election,
                    'position': vote_data['position'],
                    'candidate': vote_data['candidate'],
                }
                
                # Determine if voting as member or owner
                if election.organization.owner == request.user:
                    vote_create_data['voter_user'] = request.user
                else:
                    member = OrganizationMember.objects.get(
                        user=request.user,
                        organization=election.organization,
                        membership_status='approved'
                    )
                    vote_create_data['voter'] = member
                
                vote = Vote.objects.create(**vote_create_data)
                votes_created.append(vote)
        
        return Response(
            VoteSerializer(votes_created, many=True).data,
            status=status.HTTP_201_CREATED
        )
    
    @extend_schema(
        description='Get election results',
        responses={200: ElectionResultSerializer(many=True)}
    )
    @action(detail=False, methods=['get'])
    def results(self, request):
        """Get results for an election."""
        election_id = request.query_params.get('election_id')
        if not election_id:
            return Response(
                {'error': 'election_id parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        election = get_object_or_404(Election, id=election_id)
        
        # Check if user can view results
        if not election.can_view_results(request.user):
            return Response(
                {'error': 'You do not have permission to view these results.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        results = Vote.get_results_for_election(election)
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'position_id': result['position'].id,
                'position_title': result['position'].title,
                'total_votes': result['total_votes'],
                'candidates': result['candidates']
            })
        
        return Response(formatted_results)
    
    @extend_schema(
        description='Get results for a specific position',
        responses={200: dict}
    )
    @action(detail=False, methods=['get'])
    def position_results(self, request):
        """Get results for a specific position."""
        position_id = request.query_params.get('position_id')
        if not position_id:
            return Response(
                {'error': 'position_id parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        from elections.models import Position
        position = get_object_or_404(Position, id=position_id)
        election = position.election
        
        # Check if user can view results
        if not election.can_view_results(request.user):
            return Response(
                {'error': 'You do not have permission to view these results.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        result = Vote.get_results_for_position(position)
        
        return Response({
            'position_id': result['position'].id,
            'position_title': result['position'].title,
            'total_votes': result['total_votes'],
            'candidates': result['candidates']
        })