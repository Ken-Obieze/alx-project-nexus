from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.core.exceptions import ValidationError


class OrganizationStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    SUSPENDED = 'suspended', 'Suspended'


class Organization(models.Model):
    """Organization model for managing polling organizations."""
    
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_organizations',
        null=False
    )
    status = models.CharField(
        max_length=20,
        choices=OrganizationStatus.choices,
        default=OrganizationStatus.ACTIVE
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'organizations'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['owner']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Auto-generate slug if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
            # Ensure unique slug
            original_slug = self.slug
            counter = 1
            while Organization.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    def get_member_count(self):
        """Get total approved members count."""
        return self.members.filter(membership_status=MembershipStatus.APPROVED).count()
    
    def get_admin_count(self):
        """Get total admin count."""
        return self.members.filter(
            membership_status=MembershipStatus.APPROVED,
            role=MemberRole.ADMIN
        ).count()
    
    def is_member(self, user):
        """Check if user is an approved member."""
        return self.members.filter(
            user=user,
            membership_status=MembershipStatus.APPROVED
        ).exists()
    
    def is_admin(self, user):
        """Check if user is an admin of this organization."""
        if self.owner == user:
            return True
        return self.members.filter(
            user=user,
            role=MemberRole.ADMIN,
            membership_status=MembershipStatus.APPROVED
        ).exists()
    
    def can_manage(self, user):
        """Check if user can manage this organization."""
        return user.is_super_admin() or self.owner == user or self.is_admin(user)
    
    def suspend(self):
        """Suspend the organization."""
        self.status = OrganizationStatus.SUSPENDED
        self.save(update_fields=['status', 'updated_at'])
    
    def activate(self):
        """Activate the organization."""
        self.status = OrganizationStatus.ACTIVE
        self.save(update_fields=['status', 'updated_at'])


class MembershipStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    APPROVED = 'approved', 'Approved'
    REJECTED = 'rejected', 'Rejected'


class MemberRole(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    VOTER = 'voter', 'Voter'


class OrganizationMember(models.Model):
    """Organization membership model."""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='organization_memberships'
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='members'
    )
    role = models.CharField(
        max_length=20,
        choices=MemberRole.choices,
        default=MemberRole.VOTER
    )
    membership_status = models.CharField(
        max_length=20,
        choices=MembershipStatus.choices,
        default=MembershipStatus.PENDING
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invited_members'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'organization_members'
        ordering = ['-created_at']
        unique_together = [['user', 'organization']]
        indexes = [
            models.Index(fields=['user', 'organization']),
            models.Index(fields=['organization', 'membership_status']),
            models.Index(fields=['membership_status']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.organization.name} ({self.role})"
    
    def clean(self):
        """Validate membership."""
        # Check if user is organization owner
        if self.user == self.organization.owner:
            raise ValidationError(
                "Organization owner cannot be added as a member. They have full access by default."
            )
    
    def save(self, *args, **kwargs):
        """Override save to validate."""
        self.clean()
        super().save(*args, **kwargs)
    
    def approve(self):
        """Approve membership request."""
        self.membership_status = MembershipStatus.APPROVED
        self.save(update_fields=['membership_status', 'updated_at'])
    
    def reject(self):
        """Reject membership request."""
        self.membership_status = MembershipStatus.REJECTED
        self.save(update_fields=['membership_status', 'updated_at'])
    
    def promote_to_admin(self):
        """Promote member to admin role."""
        if self.membership_status == MembershipStatus.APPROVED:
            self.role = MemberRole.ADMIN
            self.save(update_fields=['role', 'updated_at'])
        else:
            raise ValidationError("Can only promote approved members.")
    
    def demote_to_voter(self):
        """Demote admin to voter role."""
        self.role = MemberRole.VOTER
        self.save(update_fields=['role', 'updated_at'])