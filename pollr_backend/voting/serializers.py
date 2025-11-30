from rest_framework import serializers
from .models import Vote


class VoteSerializer(serializers.ModelSerializer):
    """Serializer for Vote model."""
    
    election_title = serializers.CharField(source='election.title', read_only=True)
    position_title = serializers.CharField(source='position.title', read_only=True)
    candidate_name = serializers.CharField(source='candidate.name', read_only=True)
    
    class Meta:
        model = Vote
        fields = [
            'id', 'election', 'election_title', 'position', 'position_title',
            'candidate', 'candidate_name', 'vote_token', 'created_at'
        ]
        read_only_fields = ['id', 'vote_token', 'created_at']


class CastVoteSerializer(serializers.Serializer):
    """Serializer for casting a vote."""
    
    position_id = serializers.IntegerField()
    candidate_id = serializers.IntegerField()
    
    def validate(self, attrs):
        """Validate vote casting."""
        from elections.models import Position, Candidate
        
        position_id = attrs['position_id']
        candidate_id = attrs['candidate_id']
        election = self.context['election']
        user = self.context['request'].user
        
        # Validate position exists and belongs to election
        try:
            position = Position.objects.get(id=position_id, election=election)
        except Position.DoesNotExist:
            raise serializers.ValidationError({
                'position_id': 'Position does not exist in this election.'
            })
        
        # Validate candidate exists and belongs to position
        try:
            candidate = Candidate.objects.get(id=candidate_id, position=position)
        except Candidate.DoesNotExist:
            raise serializers.ValidationError({
                'candidate_id': 'Candidate does not exist for this position.'
            })
        
        # Check if user has already voted for this position
        if Vote.has_user_voted_for_position(election, position, user):
            raise serializers.ValidationError({
                'position_id': 'You have already voted for this position.'
            })
        
        # Check if election is active
        if not election.can_vote():
            raise serializers.ValidationError(
                'Voting is not currently allowed for this election.'
            )
        
        # Check if user is eligible to vote (member or owner)
        if not election.organization.is_member(user) and election.organization.owner != user:
            raise serializers.ValidationError(
                'You are not eligible to vote in this election.'
            )
        
        attrs['position'] = position
        attrs['candidate'] = candidate
        return attrs


class BulkVoteSerializer(serializers.Serializer):
    """Serializer for casting multiple votes at once."""
    
    votes = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField()
        ),
        min_length=1
    )
    
    def validate(self, attrs):
        """Validate bulk votes."""
        from elections.models import Position, Candidate
        
        election = self.context['election']
        user = self.context['request'].user
        votes_data = attrs['votes']
        
        # Check if election is active
        if not election.can_vote():
            raise serializers.ValidationError(
                'Voting is not currently allowed for this election.'
            )
        
        # Check if user is eligible to vote
        if not election.organization.is_member(user) and election.organization.owner != user:
            raise serializers.ValidationError(
                'You are not eligible to vote in this election.'
            )
        
        validated_votes = []
        position_ids_seen = set()
        
        for vote_data in votes_data:
            position_id = vote_data.get('position_id')
            candidate_id = vote_data.get('candidate_id')
            
            if not position_id or not candidate_id:
                raise serializers.ValidationError(
                    'Each vote must have position_id and candidate_id.'
                )
            
            # Check for duplicate positions in request
            if position_id in position_ids_seen:
                raise serializers.ValidationError(
                    f'Cannot vote multiple times for position {position_id}.'
                )
            position_ids_seen.add(position_id)
            
            # Validate position
            try:
                position = Position.objects.get(id=position_id, election=election)
            except Position.DoesNotExist:
                raise serializers.ValidationError(
                    f'Position {position_id} does not exist in this election.'
                )
            
            # Validate candidate
            try:
                candidate = Candidate.objects.get(id=candidate_id, position=position)
            except Candidate.DoesNotExist:
                raise serializers.ValidationError(
                    f'Candidate {candidate_id} does not exist for position {position_id}.'
                )
            
            # Check if already voted
            if Vote.has_user_voted_for_position(election, position, user):
                raise serializers.ValidationError(
                    f'You have already voted for position: {position.title}'
                )
            
            validated_votes.append({
                'position': position,
                'candidate': candidate
            })
        
        attrs['validated_votes'] = validated_votes
        return attrs


class ElectionResultSerializer(serializers.Serializer):
    """Serializer for election results."""
    
    position_id = serializers.IntegerField()
    position_title = serializers.CharField()
    total_votes = serializers.IntegerField()
    candidates = serializers.ListField(
        child=serializers.DictField()
    )


class PositionResultSerializer(serializers.Serializer):
    """Serializer for position-specific results."""
    
    candidate_id = serializers.IntegerField()
    candidate_name = serializers.CharField()
    vote_count = serializers.IntegerField()
    percentage = serializers.FloatField()