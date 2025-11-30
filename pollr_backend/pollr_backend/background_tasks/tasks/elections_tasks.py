from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from elections.models import Election, ElectionStatus


@shared_task
def update_election_statuses():
    """
    Periodic task to update election statuses based on current time.
    Runs every 5 minutes via Celery Beat.
    """
    now = timezone.now()
    updated_count = 0
    
    # Update scheduled elections to ongoing
    scheduled_elections = Election.objects.filter(
        status=ElectionStatus.SCHEDULED,
        start_at__lte=now,
        end_at__gt=now
    )
    for election in scheduled_elections:
        election.status = ElectionStatus.ONGOING
        election.save(update_fields=['status', 'updated_at'])
        
        # Send notification that election has started
        send_election_started_notification.delay(election.id)
        updated_count += 1
    
    # Update ongoing elections to completed
    ongoing_elections = Election.objects.filter(
        status=ElectionStatus.ONGOING,
        end_at__lte=now
    )
    for election in ongoing_elections:
        election.status = ElectionStatus.COMPLETED
        election.save(update_fields=['status', 'updated_at'])
        
        # Send notification that election has ended
        send_election_ended_notification.delay(election.id)
        updated_count += 1
    
    return f"Updated {updated_count} elections"


@shared_task
def send_election_reminders():
    """
    Send reminders for elections starting soon or ending soon.
    Runs daily at 9 AM via Celery Beat.
    """
    now = timezone.now()
    tomorrow = now + timedelta(days=1)
    
    # Elections starting tomorrow
    upcoming_elections = Election.objects.filter(
        status=ElectionStatus.SCHEDULED,
        start_at__gte=now,
        start_at__lt=tomorrow
    )
    
    for election in upcoming_elections:
        send_election_starting_soon_email.delay(election.id)
    
    # Elections ending tomorrow
    ending_elections = Election.objects.filter(
        status=ElectionStatus.ONGOING,
        end_at__gte=now,
        end_at__lt=tomorrow
    )
    
    for election in ending_elections:
        send_election_ending_soon_email.delay(election.id)
    
    return f"Sent reminders for {upcoming_elections.count() + ending_elections.count()} elections"


@shared_task
def send_election_started_notification(election_id):
    """Send notification when election starts."""
    try:
        election = Election.objects.get(id=election_id)
        organization = election.organization
        
        # Get all members and owner
        recipients = []
        recipients.append(organization.owner.email)
        
        members = organization.members.filter(membership_status='approved')
        for member in members:
            recipients.append(member.user.email)
        
        subject = f"Election Started: {election.title}"
        message = f"""
Hello,

The election "{election.title}" has started in {organization.name}.

You can now cast your vote.

Election ends at: {election.end_at.strftime('%Y-%m-%d %H:%M')}

Best regards,
PollR Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=False,
        )
        
        return f"Sent started notification for election {election_id}"
    except Exception as e:
        return f"Error sending notification: {str(e)}"


@shared_task
def send_election_ended_notification(election_id):
    """Send notification when election ends."""
    try:
        election = Election.objects.get(id=election_id)
        organization = election.organization
        
        # Get all members and owner
        recipients = []
        recipients.append(organization.owner.email)
        
        members = organization.members.filter(membership_status='approved')
        for member in members:
            recipients.append(member.user.email)
        
        subject = f"Election Completed: {election.title}"
        message = f"""
Hello,

The election "{election.title}" in {organization.name} has ended.

Total votes cast: {election.get_total_votes()}
Voter turnout: {election.get_voter_turnout():.2f}%

{"Results are now available." if election.result_visibility == 'public' else "Results are private to organization members."}

Best regards,
PollR Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=False,
        )
        
        return f"Sent ended notification for election {election_id}"
    except Exception as e:
        return f"Error sending notification: {str(e)}"


@shared_task
def send_election_starting_soon_email(election_id):
    """Send reminder that election starts soon."""
    try:
        election = Election.objects.get(id=election_id)
        organization = election.organization
        
        recipients = []
        recipients.append(organization.owner.email)
        
        members = organization.members.filter(membership_status='approved')
        for member in members:
            recipients.append(member.user.email)
        
        subject = f"Reminder: Election Starting Soon - {election.title}"
        message = f"""
Hello,

This is a reminder that the election "{election.title}" in {organization.name} will start soon.

Starts at: {election.start_at.strftime('%Y-%m-%d %H:%M')}
Ends at: {election.end_at.strftime('%Y-%m-%d %H:%M')}

Make sure you're ready to vote!

Best regards,
PollR Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=False,
        )
        
        return f"Sent starting soon email for election {election_id}"
    except Exception as e:
        return f"Error sending email: {str(e)}"


@shared_task
def send_election_ending_soon_email(election_id):
    """Send reminder that election ends soon."""
    try:
        election = Election.objects.get(id=election_id)
        organization = election.organization
        
        recipients = []
        recipients.append(organization.owner.email)
        
        members = organization.members.filter(membership_status='approved')
        for member in members:
            recipients.append(member.user.email)
        
        subject = f"Last Chance to Vote: {election.title}"
        message = f"""
Hello,

This is your last chance to vote in "{election.title}" for {organization.name}.

The election ends at: {election.end_at.strftime('%Y-%m-%d %H:%M')}

If you haven't voted yet, please do so now!

Best regards,
PollR Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=False,
        )
        
        return f"Sent ending soon email for election {election_id}"
    except Exception as e:
        return f"Error sending email: {str(e)}"


@shared_task
def send_election_created_notification(election_id):
    """Send notification when new election is created."""
    try:
        election = Election.objects.get(id=election_id)
        organization = election.organization
        
        recipients = []
        members = organization.members.filter(membership_status='approved')
        for member in members:
            recipients.append(member.user.email)
        
        if not recipients:
            return "No recipients found"
        
        subject = f"New Election: {election.title}"
        message = f"""
Hello,

A new election "{election.title}" has been created in {organization.name}.

Description: {election.description}
Starts at: {election.start_at.strftime('%Y-%m-%d %H:%M')}
Ends at: {election.end_at.strftime('%Y-%m-%d %H:%M')}

Get ready to vote!

Best regards,
PollR Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipients,
            fail_silently=False,
        )
        
        return f"Sent creation notification for election {election_id}"
    except Exception as e:
        return f"Error sending notification: {str(e)}"