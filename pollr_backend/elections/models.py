from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone


class ElectionStatus(models.TextChoices):
    SCHEDULED = 'scheduled', 'Scheduled'
    ONGOING = 'ongoing', 'Ongoing'
    COMPLETED = 'completed', 'Completed'


class ResultVisibility(models.TextChoices):
    PUBLIC = 'public', 'Public'
    PRIVATE = 'private', 'Private'


class Election(models.Model):
    """Election model for managing polls/elections."""
    
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='elections'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=ElectionStatus.choices,
        default=ElectionStatus.SCHEDULED
    )
    result_visibility = models.CharField(
        max_length=20,
        choices=ResultVisibility.choices,
        default=ResultVisibility.PUBLIC
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'elections'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['status']),
            models.Index(fields=['start_at', 'end_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.organization.name}"
    
    def clean(self):
        """Validate election dates."""
        if self.start_at and self.end_at and self.start_at >= self.end_at:
            raise ValidationError("End time must be after start time.")
    
    def save(self, *args, **kwargs):
        """Override save to validate and update status."""
        self.clean()
        self.update_status()
        super().save(*args, **kwargs)
    
    def update_status(self):
        """Update election status based on current time."""
        now = timezone.now()
        
        if self.status == ElectionStatus.COMPLETED:
            # Don't change completed status
            return
        
        if now < self.start_at:
            self.status = ElectionStatus.SCHEDULED
        elif self.start_at <= now < self.end_at:
            self.status = ElectionStatus.ONGOING
        elif now >= self.end_at:
            self.status = ElectionStatus.COMPLETED
    
    def is_active(self):
        """Check if election is currently active."""
        self.update_status()
        return self.status == ElectionStatus.ONGOING
    
    def can_vote(self):
        """Check if voting is allowed."""
        return self.is_active()
    
    def can_view_results(self, user):
        """Check if user can view results."""
        if self.result_visibility == ResultVisibility.PUBLIC:
            return True
        
        # Private results: only org members can view
        if self.status != ElectionStatus.COMPLETED:
            # Results not ready yet
            return False
        
        return self.organization.is_member(user) or self.organization.owner == user
    
    def get_total_votes(self):
        """Get total number of votes cast."""
        from voting.models import Vote
        return Vote.objects.filter(election=self).count()
    
    def get_voter_turnout(self):
        """Get voter turnout percentage."""
        from voting.models import Vote
        total_eligible = self.organization.get_member_count() + 1  # +1 for owner
        if total_eligible == 0:
            return 0
        
        total_voters = Vote.objects.filter(election=self).values('voter').distinct().count()
        return (total_voters / total_eligible) * 100
    
    def start(self):
        """Manually start an election."""
        if self.status == ElectionStatus.SCHEDULED:
            self.status = ElectionStatus.ONGOING
            super().save(update_fields=['status', 'updated_at'])
    
    def end(self):
        """Manually end an election."""
        if self.status in [ElectionStatus.SCHEDULED, ElectionStatus.ONGOING]:
            self.status = ElectionStatus.COMPLETED
            super().save(update_fields=['status', 'updated_at'])


class Position(models.Model):
    """Position model for election positions/categories."""
    
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name='positions'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order_index = models.IntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'positions'
        ordering = ['order_index', 'created_at']
        indexes = [
            models.Index(fields=['election', 'order_index']),
        ]
        unique_together = [['election', 'title']]
    
    def __str__(self):
        return f"{self.title} - {self.election.title}"
    
    def get_candidates_count(self):
        """Get number of candidates for this position."""
        return self.candidates.count()
    
    def get_total_votes(self):
        """Get total votes for this position."""
        from .voting.models import Vote
        return Vote.objects.filter(position=self).count()


class Candidate(models.Model):
    """Candidate model for election candidates."""
    
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        related_name='candidates'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='candidacies'
    )
    name = models.CharField(max_length=255)
    manifesto = models.TextField(blank=True)
    photo_url = models.URLField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'candidates'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['position']),
            models.Index(fields=['user']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.position.title}"
    
    def clean(self):
        """Validate candidate."""
        # If user is provided, ensure they're a member of the organization
        if self.user:
            election = self.position.election
            if not election.organization.is_member(self.user) and election.organization.owner != self.user:
                raise ValidationError(
                    "Candidate must be a member of the organization."
                )
    
    def save(self, *args, **kwargs):
        """Override save to auto-populate name from user if not provided."""
        if self.user and not self.name:
            self.name = self.user.full_name
        self.clean()
        super().save(*args, **kwargs)
    
    def get_vote_count(self):
        """Get number of votes for this candidate."""
        from voting.models import Vote
        return Vote.objects.filter(candidate=self).count()
    
    def get_vote_percentage(self):
        """Get percentage of votes for this candidate."""
        total_votes = self.position.get_total_votes()
        if total_votes == 0:
            return 0
        return (self.get_vote_count() / total_votes) * 100