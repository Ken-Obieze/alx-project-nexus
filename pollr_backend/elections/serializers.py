from rest_framework import serializers
from django.utils import timezone
from django.db import models
from .models import Election, Position, Candidate


class CandidateSerializer(serializers.ModelSerializer):
    """Serializer for Candidate model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    position_title = serializers.CharField(source='position.title', read_only=True)
    vote_count = serializers.SerializerMethodField()
    vote_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Candidate
        fields = [
            'id', 'position', 'position_title', 'user', 'user_email',
            'name', 'manifesto', 'photo_url', 'vote_count', 'vote_percentage',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'vote_count', 'vote_percentage', 'created_at', 'updated_at']
    
    def get_vote_count(self, obj):
        """Get vote count for candidate."""
        # Only show if election is completed
        if obj.position.election.status == 'completed':
            return obj.get_vote_count()
        return None
    
    def get_vote_percentage(self, obj):
        """Get vote percentage for candidate."""
        # Only show if election is completed
        if obj.position.election.status == 'completed':
            return round(obj.get_vote_percentage(), 2)
        return None


class PositionSerializer(serializers.ModelSerializer):
    """Serializer for Position model."""
    
    election_title = serializers.CharField(source='election.title', read_only=True)
    candidates_count = serializers.SerializerMethodField()
    total_votes = serializers.SerializerMethodField()
    
    class Meta:
        model = Position
        fields = [
            'id', 'election', 'election_title', 'title', 'description',
            'order_index', 'candidates_count', 'total_votes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'candidates_count', 'total_votes', 'created_at', 'updated_at']
    
    def get_candidates_count(self, obj):
        """Get number of candidates."""
        return obj.get_candidates_count()
    
    def get_total_votes(self, obj):
        """Get total votes for position."""
        # Only show if election is completed
        if obj.election.status == 'completed':
            return obj.get_total_votes()
        return None


class PositionDetailSerializer(PositionSerializer):
    """Detailed serializer for Position with candidates."""
    
    candidates = CandidateSerializer(many=True, read_only=True)
    
    class Meta(PositionSerializer.Meta):
        fields = PositionSerializer.Meta.fields + ['candidates']


class ElectionSerializer(serializers.ModelSerializer):
    """Serializer for Election model."""
    
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    organization_slug = serializers.CharField(source='organization.slug', read_only=True)
    positions_count = serializers.SerializerMethodField()
    total_votes = serializers.SerializerMethodField()
    voter_turnout = serializers.SerializerMethodField()
    can_vote = serializers.SerializerMethodField()
    can_view_results = serializers.SerializerMethodField()
    has_voted = serializers.SerializerMethodField()
    
    class Meta:
        model = Election
        fields = [
            'id', 'organization', 'organization_name', 'organization_slug',
            'title', 'description', 'start_at', 'end_at', 'status',
            'result_visibility', 'positions_count', 'total_votes',
            'voter_turnout', 'can_vote', 'can_view_results', 'has_voted',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at']
    
    def validate(self, attrs):
        """Validate election dates."""
        start_at = attrs.get('start_at')
        end_at = attrs.get('end_at')
        
        if start_at and end_at and start_at >= end_at:
            raise serializers.ValidationError({
                'end_at': 'End time must be after start time.'
            })
        
        return attrs
    
    def get_positions_count(self, obj):
        """Get number of positions."""
        return obj.positions.count()
    
    def get_total_votes(self, obj):
        """Get total votes cast."""
        return obj.get_total_votes()
    
    def get_voter_turnout(self, obj):
        """Get voter turnout percentage."""
        return round(obj.get_voter_turnout(), 2)
    
    def get_can_vote(self, obj):
        """Check if user can vote."""
        return obj.can_vote()
    
    def get_can_view_results(self, obj):
        """Check if user can view results."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.can_view_results(request.user)
        return False
    
    def get_has_voted(self, obj):
        """Check if current user has voted."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from voting.models import Vote
            return Vote.objects.filter(
                election=obj
            ).filter(
                models.Q(voter__user=request.user) | models.Q(voter_user=request.user)
            ).exists()
        return False


class ElectionDetailSerializer(ElectionSerializer):
    """Detailed serializer for Election with positions."""
    
    positions = PositionDetailSerializer(many=True, read_only=True)
    
    class Meta(ElectionSerializer.Meta):
        fields = ElectionSerializer.Meta.fields + ['positions']


class ElectionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating elections."""
    
    class Meta:
        model = Election
        fields = [
            'organization', 'title', 'description',
            'start_at', 'end_at', 'result_visibility'
        ]
    
    def validate(self, attrs):
        """Validate election creation."""
        # Validate dates
        if attrs['start_at'] >= attrs['end_at']:
            raise serializers.ValidationError({
                'end_at': 'End time must be after start time.'
            })
        
        # Validate organization access
        request = self.context.get('request')
        organization = attrs['organization']
        if not organization.can_manage(request.user):
            raise serializers.ValidationError({
                'organization': 'You do not have permission to create elections for this organization.'
            })
        
        return attrs


class CandidateCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating candidates."""
    
    name = serializers.CharField(required=False)
    
    class Meta:
        model = Candidate
        fields = ['position', 'user', 'name', 'manifesto', 'photo_url']
    
    def validate(self, attrs):
        """Validate candidate creation."""
        position = attrs['position']
        user = attrs.get('user')
        
        # If user is provided, check they're a member
        if user:
            election = position.election
            if not election.organization.is_member(user) and election.organization.owner != user:
                raise serializers.ValidationError({
                    'user': 'Candidate must be a member of the organization.'
                })
            
            # Auto-populate name from user if not provided
            if not attrs.get('name'):
                attrs['name'] = user.full_name
        
        # Name is required if no user
        if not user and not attrs.get('name'):
            raise serializers.ValidationError({
                'name': 'Name is required for external candidates.'
            })
        
        return attrs