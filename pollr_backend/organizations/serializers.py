from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Organization, OrganizationMember, MembershipStatus, MemberRole

User = get_user_model()


class OrganizationSerializer(serializers.ModelSerializer):
    """Serializer for Organization model."""
    
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    member_count = serializers.SerializerMethodField()
    admin_count = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()
    is_admin = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()
    
    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'slug', 'description', 'owner', 'owner_email',
            'owner_name', 'status', 'member_count', 'admin_count',
            'is_owner', 'is_admin', 'is_member',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'owner', 'slug', 'created_at', 'updated_at']
    
    def get_member_count(self, obj):
        """Get approved member count."""
        return obj.get_member_count()
    
    def get_admin_count(self, obj):
        """Get admin count."""
        return obj.get_admin_count()
    
    def get_is_owner(self, obj):
        """Check if current user is owner."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.owner == request.user
        return False
    
    def get_is_admin(self, obj):
        """Check if current user is admin."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_admin(request.user)
        return False
    
    def get_is_member(self, obj):
        """Check if current user is member."""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.is_member(request.user)
        return False
    
    def create(self, validated_data):
        """Create organization with current user as owner."""
        request = self.context.get('request')
        validated_data['owner'] = request.user
        return super().create(validated_data)


class OrganizationDetailSerializer(OrganizationSerializer):
    """Detailed serializer with member list."""
    
    members = serializers.SerializerMethodField()
    
    class Meta(OrganizationSerializer.Meta):
        fields = OrganizationSerializer.Meta.fields + ['members']
    
    def get_members(self, obj):
        """Get approved members only."""
        members = obj.members.filter(membership_status=MembershipStatus.APPROVED)
        return OrganizationMemberSerializer(members, many=True).data


class OrganizationMemberSerializer(serializers.ModelSerializer):
    """Serializer for OrganizationMember model."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True)
    invited_by_email = serializers.EmailField(source='invited_by.email', read_only=True)
    
    class Meta:
        model = OrganizationMember
        fields = [
            'id', 'user', 'user_email', 'user_name', 'organization',
            'organization_name', 'role', 'membership_status',
            'invited_by', 'invited_by_email', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'invited_by', 'created_at', 'updated_at']


class MembershipRequestSerializer(serializers.Serializer):
    """Serializer for membership requests."""
    
    user_email = serializers.EmailField()
    role = serializers.ChoiceField(
        choices=MemberRole.choices,
        default=MemberRole.VOTER
    )
    
    def validate_user_email(self, value):
        """Validate that user exists."""
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return value
    
    def validate(self, attrs):
        """Validate membership request."""
        organization = self.context.get('organization')
        user = User.objects.get(email=attrs['user_email'])
        
        # Check if user is the owner
        if organization.owner == user:
            raise serializers.ValidationError(
                "Cannot add organization owner as a member. They have full access."
            )
        
        # Check if membership already exists
        if OrganizationMember.objects.filter(
            user=user,
            organization=organization
        ).exists():
            raise serializers.ValidationError(
                "User is already a member or has a pending request."
            )
        
        attrs['user'] = user
        return attrs


class MembershipJoinSerializer(serializers.Serializer):
    """Serializer for joining an organization."""
    
    organization_slug = serializers.SlugField()
    
    def validate_organization_slug(self, value):
        """Validate organization exists."""
        try:
            Organization.objects.get(slug=value)
        except Organization.DoesNotExist:
            raise serializers.ValidationError("Organization not found.")
        return value


class MembershipActionSerializer(serializers.Serializer):
    """Serializer for membership actions (approve/reject)."""
    
    action = serializers.ChoiceField(choices=['approve', 'reject'])


class MemberRoleUpdateSerializer(serializers.Serializer):
    """Serializer for updating member role."""
    
    role = serializers.ChoiceField(choices=MemberRole.choices)


class OrganizationStatisticsSerializer(serializers.Serializer):
    """Serializer for organization statistics."""
    
    total_members = serializers.IntegerField()
    approved_members = serializers.IntegerField()
    pending_members = serializers.IntegerField()
    rejected_members = serializers.IntegerField()
    admin_count = serializers.IntegerField()
    voter_count = serializers.IntegerField()
    total_elections = serializers.IntegerField()
    active_elections = serializers.IntegerField()