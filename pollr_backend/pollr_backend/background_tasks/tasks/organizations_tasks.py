from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from organizations.models import Organization, OrganizationMember


@shared_task
def send_membership_invitation_email(member_id):
    """Send email when user is invited to join organization."""
    try:
        member = OrganizationMember.objects.select_related(
            'user',
            'organization',
            'invited_by'
        ).get(id=member_id)
        
        subject = f"Invitation to join {member.organization.name}"
        message = f"""
Hello {member.user.full_name},

{"" if not member.invited_by else f"{member.invited_by.full_name} has "}invited you to join {member.organization.name} on PollR.

Organization: {member.organization.name}
Description: {member.organization.description}
Role: {member.get_role_display()}

Please log in to accept or decline this invitation.

Best regards,
PollR Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [member.user.email],
            fail_silently=False,
        )
        
        return f"Sent invitation email to {member.user.email}"
    except Exception as e:
        return f"Error sending email: {str(e)}"


@shared_task
def send_membership_approved_email(member_id):
    """Send email when membership is approved."""
    try:
        member = OrganizationMember.objects.select_related(
            'user',
            'organization'
        ).get(id=member_id)
        
        subject = f"Membership Approved - {member.organization.name}"
        message = f"""
Hello {member.user.full_name},

Good news! Your membership request for {member.organization.name} has been approved.

You are now a {member.get_role_display()} and can participate in elections.

Best regards,
PollR Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [member.user.email],
            fail_silently=False,
        )
        
        return f"Sent approval email to {member.user.email}"
    except Exception as e:
        return f"Error sending email: {str(e)}"


@shared_task
def send_membership_rejected_email(member_id):
    """Send email when membership is rejected."""
    try:
        member = OrganizationMember.objects.select_related(
            'user',
            'organization'
        ).get(id=member_id)
        
        subject = f"Membership Request - {member.organization.name}"
        message = f"""
Hello {member.user.full_name},

Your membership request for {member.organization.name} has been reviewed.

Unfortunately, your request was not approved at this time.

Best regards,
PollR Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [member.user.email],
            fail_silently=False,
        )
        
        return f"Sent rejection email to {member.user.email}"
    except Exception as e:
        return f"Error sending email: {str(e)}"


@shared_task
def send_role_updated_email(member_id, old_role, new_role):
    """Send email when member role is updated."""
    try:
        member = OrganizationMember.objects.select_related(
            'user',
            'organization'
        ).get(id=member_id)
        
        subject = f"Role Updated - {member.organization.name}"
        message = f"""
Hello {member.user.full_name},

Your role in {member.organization.name} has been updated.

Previous role: {old_role.title()}
New role: {new_role.title()}

{"You now have administrative privileges in this organization." if new_role == 'admin' else ""}

Best regards,
PollR Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [member.user.email],
            fail_silently=False,
        )
        
        return f"Sent role update email to {member.user.email}"
    except Exception as e:
        return f"Error sending email: {str(e)}"


@shared_task
def notify_admins_of_join_request(member_id):
    """Notify organization admins of new join request."""
    try:
        member = OrganizationMember.objects.select_related(
            'user',
            'organization',
            'organization__owner'
        ).get(id=member_id)
        
        organization = member.organization
        
        # Get all admins
        admin_emails = [organization.owner.email]
        admin_members = organization.members.filter(
            role='admin',
            membership_status='approved'
        )
        for admin in admin_members:
            admin_emails.append(admin.user.email)
        
        subject = f"New Join Request - {organization.name}"
        message = f"""
Hello,

{member.user.full_name} ({member.user.email}) has requested to join {organization.name}.

Please review and approve or reject this request.

Best regards,
PollR Team
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            admin_emails,
            fail_silently=False,
        )
        
        return f"Notified {len(admin_emails)} admins about join request"
    except Exception as e:
        return f"Error sending notification: {str(e)}"