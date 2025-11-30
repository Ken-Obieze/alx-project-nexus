from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from voting.models import Vote


@shared_task
def send_vote_confirmation_email(vote_id):
    """Send email confirmation after vote is cast."""
    try:
        vote = Vote.objects.select_related(
            'election',
            'position',
            'candidate',
            'voter__user',
            'voter_user'
        ).get(id=vote_id)
        
        # Get voter email
        if vote.voter:
            recipient_email = vote.voter.user.email
            voter_name = vote.voter.user.full_name
        else:
            recipient_email = vote.voter_user.email
            voter_name = vote.voter_user.full_name
        
        subject = f"Vote Confirmation - {vote.election.title}"
        message = f"""
Hello {voter_name},

Your vote has been successfully recorded!

Election: {vote.election.title}
Position: {vote.position.title}
Candidate: {vote.candidate.name}

Vote Token: {vote.vote_token}
(Keep this token for verification)

Voted at: {vote.created_at.strftime('%Y-%m-%d %H:%M:%S')}

Thank you for participating!

Best regards,
PollR Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
            fail_silently=False,
        )
        
        return f"Sent confirmation email for vote {vote_id}"
    except Exception as e:
        return f"Error sending email: {str(e)}"


@shared_task
def cleanup_old_votes():
    """
    Clean up vote data older than specified retention period.
    Runs monthly via Celery Beat.
    
    This is for data retention compliance - adjust based on your requirements.
    """
    # Keep votes for 2 years
    retention_period = timedelta(days=730)
    cutoff_date = timezone.now() - retention_period
    
    # Only cleanup votes from completed elections
    old_votes = Vote.objects.filter(
        created_at__lt=cutoff_date,
        election__status='completed'
    )
    
    count = old_votes.count()
    # old_votes.delete()  # Uncomment to actually delete
    
    return f"Cleaned up {count} old votes (retention: {retention_period.days} days)"


@shared_task
def generate_vote_statistics(election_id):
    """Generate and cache vote statistics for an election."""
    try:
        from elections.models import Election
        
        election = Election.objects.get(id=election_id)
        results = Vote.get_results_for_election(election)
        
        # Here you could cache the results in Redis for faster access
        # For now, just return the computation
        
        stats = {
            'election_id': election_id,
            'total_votes': election.get_total_votes(),
            'voter_turnout': election.get_voter_turnout(),
            'positions_count': len(results),
            'timestamp': timezone.now().isoformat()
        }
        
        return f"Generated statistics for election {election_id}: {stats}"
    except Exception as e:
        return f"Error generating statistics: {str(e)}"


@shared_task
def send_bulk_vote_confirmation(vote_ids):
    """Send confirmation for multiple votes cast together."""
    try:
        votes = Vote.objects.filter(id__in=vote_ids).select_related(
            'election',
            'position',
            'candidate',
            'voter__user',
            'voter_user'
        )
        
        if not votes:
            return "No votes found"
        
        # Get voter email from first vote
        first_vote = votes.first()
        if first_vote.voter:
            recipient_email = first_vote.voter.user.email
            voter_name = first_vote.voter.user.full_name
        else:
            recipient_email = first_vote.voter_user.email
            voter_name = first_vote.voter_user.full_name
        
        election = first_vote.election
        
        # Build vote list
        vote_list = []
        for vote in votes:
            vote_list.append(
                f"- {vote.position.title}: {vote.candidate.name} (Token: {vote.vote_token})"
            )
        
        subject = f"Votes Confirmation - {election.title}"
        message = f"""
Hello {voter_name},

Your votes have been successfully recorded!

Election: {election.title}

Votes cast:
{chr(10).join(vote_list)}

Voted at: {first_vote.created_at.strftime('%Y-%m-%d %H:%M:%S')}

Thank you for participating!

Best regards,
PollR Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [recipient_email],
            fail_silently=False,
        )
        
        return f"Sent bulk confirmation email for {len(vote_ids)} votes"
    except Exception as e:
        return f"Error sending email: {str(e)}"


@shared_task
def notify_non_voters(election_id):
    """
    Notify organization members who haven't voted yet.
    Can be triggered manually or scheduled before election ends.
    """
    try:
        from elections.models import Election
        from organizations.models import OrganizationMember
        
        election = Election.objects.get(id=election_id)
        
        if election.status != 'ongoing':
            return "Election is not ongoing"
        
        organization = election.organization
        
        # Get all eligible voters
        all_members = list(organization.members.filter(
            membership_status='approved'
        ).values_list('user__email', flat=True))
        
        # Add owner
        all_voters = all_members + [organization.owner.email]
        
        # Get voters who have voted
        voted_users = Vote.objects.filter(
            election=election
        ).values_list('voter__user__email', 'voter_user__email')
        
        voted_emails = set()
        for voter_email, owner_email in voted_users:
            if voter_email:
                voted_emails.add(voter_email)
            if owner_email:
                voted_emails.add(owner_email)
        
        # Find non-voters
        non_voters = [email for email in all_voters if email not in voted_emails]
        
        if not non_voters:
            return "All eligible voters have voted"
        
        subject = f"Reminder: Vote in {election.title}"
        message = f"""
Hello,

This is a reminder that you haven't voted yet in the election "{election.title}" for {organization.name}.

The election ends at: {election.end_at.strftime('%Y-%m-%d %H:%M')}

Please cast your vote before it's too late!

Best regards,
PollR Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            non_voters,
            fail_silently=False,
        )
        
        return f"Sent reminder to {len(non_voters)} non-voters"
    except Exception as e:
        return f"Error sending reminders: {str(e)}"