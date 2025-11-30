import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class Vote(models.Model):
    """Vote model for storing cast votes."""
    election = models.ForeignKey(
        'elections.Election',
        on_delete=models.CASCADE,
        related_name='votes'
    )
    position = models.ForeignKey(
        'elections.Position',
        on_delete=models.CASCADE,
        related_name='votes'
    )
    candidate = models.ForeignKey(
        'elections.Candidate',
        on_delete=models.CASCADE,
        related_name='votes'
    )
    voter = models.ForeignKey(
        'organizations.OrganizationMember',
        on_delete=models.CASCADE,
        related_name='votes',
        null=True,
        blank=True
    )
    # For organization owners who aren't members
    voter_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owner_votes',
        null=True,
        blank=True
    )
    vote_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'votes'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['election', 'position']),
            models.Index(fields=['candidate']),
            models.Index(fields=['voter']),
            models.Index(fields=['voter_user']),
            models.Index(fields=['created_at']),
            models.Index(fields=['vote_token']),
        ]
    
    def __str__(self):
        voter_id = self.voter_id or self.voter_user_id
        return f"Vote by {voter_id} for {self.candidate.name}"
    
    def clean(self):
        """Validate vote."""
        # Must have either voter or voter_user
        if not self.voter and not self.voter_user:
            raise ValidationError("Vote must be associated with a voter.")
        
        # Validate that position belongs to election
        if self.position.election != self.election:
            raise ValidationError("Position does not belong to this election.")
        
        # Validate that candidate belongs to position
        if self.candidate.position != self.position:
            raise ValidationError("Candidate does not belong to this position.")
        
        # Check if election is active
        if not self.election.can_vote():
            raise ValidationError("Voting is not currently allowed for this election.")
    
    def save(self, *args, **kwargs):
        """Override save to validate."""
        validate = kwargs.pop('validate', True)
        if validate:
            self.clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def has_user_voted_for_position(cls, election, position, user):
        """Check if user has already voted for a position."""
        # Check as member
        voted_as_member = cls.objects.filter(
            election=election,
            position=position,
            voter__user=user
        ).exists()
        
        # Check as owner
        voted_as_owner = cls.objects.filter(
            election=election,
            position=position,
            voter_user=user
        ).exists()
        
        return voted_as_member or voted_as_owner
    
    @classmethod
    def get_user_votes_for_election(cls, election, user):
        """Get all votes cast by user in an election."""
        return cls.objects.filter(
            models.Q(voter__user=user) | models.Q(voter_user=user),
            election=election
        )
    
    @classmethod
    def get_results_for_election(cls, election):
        """Get aggregated results for an election."""
        from django.db.models import Count
        
        results = []
        for position in election.positions.all():
            position_results = {
                'position': position,
                'total_votes': cls.objects.filter(position=position).count(),
                'candidates': []
            }
            
            # Get vote count for each candidate
            candidate_votes = cls.objects.filter(
                position=position
            ).values(
                'candidate__id',
                'candidate__name'
            ).annotate(
                vote_count=Count('id')
            ).order_by('-vote_count')
            
            for cv in candidate_votes:
                position_results['candidates'].append({
                    'candidate_id': cv['candidate__id'],
                    'candidate_name': cv['candidate__name'],
                    'vote_count': cv['vote_count'],
                    'percentage': (cv['vote_count'] / position_results['total_votes'] * 100) if position_results['total_votes'] > 0 else 0
                })
            
            # Add candidates with 0 votes
            voted_candidate_ids = [c['candidate_id'] for c in position_results['candidates']]
            for candidate in position.candidates.exclude(id__in=voted_candidate_ids):
                position_results['candidates'].append({
                    'candidate_id': candidate.id,
                    'candidate_name': candidate.name,
                    'vote_count': 0,
                    'percentage': 0
                })
            
            results.append(position_results)
        
        return results
    
    @classmethod
    def get_results_for_position(cls, position):
        """Get aggregated results for a specific position."""
        from django.db.models import Count
        
        total_votes = cls.objects.filter(position=position).count()
        
        candidate_votes = cls.objects.filter(
            position=position
        ).values(
            'candidate__id',
            'candidate__name'
        ).annotate(
            vote_count=Count('id')
        ).order_by('-vote_count')
        
        results = []
        for cv in candidate_votes:
            results.append({
                'candidate_id': cv['candidate__id'],
                'candidate_name': cv['candidate__name'],
                'vote_count': cv['vote_count'],
                'percentage': (cv['vote_count'] / total_votes * 100) if total_votes > 0 else 0
            })
        
        # Add candidates with 0 votes
        voted_candidate_ids = [r['candidate_id'] for r in results]
        for candidate in position.candidates.exclude(id__in=voted_candidate_ids):
            results.append({
                'candidate_id': candidate.id,
                'candidate_name': candidate.name,
                'vote_count': 0,
                'percentage': 0
            })
        
        return {
            'position': position,
            'total_votes': total_votes,
            'candidates': results
        }