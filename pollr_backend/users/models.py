from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserRole(models.TextChoices):
    SUPER_ADMIN = 'super_admin', 'Super Admin'
    ORG_ADMIN = 'org_admin', 'Organization Admin'
    USER = 'user', 'User'


class UserStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    SUSPENDED = 'suspended', 'Suspended'


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user."""
        if not email:
            raise ValueError('Users must have an email address')
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser."""
        extra_fields.setdefault('role', UserRole.SUPER_ADMIN)
        extra_fields.setdefault('status', UserStatus.ACTIVE)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.USER
    )
    status = models.CharField(
        max_length=20,
        choices=UserStatus.choices,
        default=UserStatus.ACTIVE
    )
    
    # Django required fields
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Add related_name to avoid clash with auth.User
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',  # Custom related_name
        related_query_name='user',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',  # Custom related_name
        related_query_name='user',
    )
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['status']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip() or self.email
    
    def is_super_admin(self):
        """Check if user is a super admin."""
        return self.role == UserRole.SUPER_ADMIN
    
    def is_org_admin(self):
        """Check if user is an organization admin."""
        return self.role == UserRole.ORG_ADMIN
    
    def can_manage_organization(self, organization):
        """Check if user can manage a specific organization."""
        if self.is_super_admin():
            return True
        return organization.owner_id == self.id or \
               organization.members.filter(
                   user=self,
                   role='admin',
                   membership_status='approved'
               ).exists()
    
    def get_organizations(self):
        """Get all organizations the user belongs to."""
        from organizations.models import Organization
        return Organization.objects.filter(
            models.Q(owner=self) |
            models.Q(members__user=self, members__membership_status='approved')
        ).distinct()
    
    def activate(self):
        """Activate the user account."""
        self.status = UserStatus.ACTIVE
        self.save(update_fields=['status', 'updated_at'])
    
    def suspend(self):
        """Suspend the user account."""
        self.status = UserStatus.SUSPENDED
        self.save(update_fields=['status', 'updated_at'])