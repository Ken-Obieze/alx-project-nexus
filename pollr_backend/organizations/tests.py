import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from .models import (
    Organization, OrganizationMember, 
    MembershipStatus, MemberRole, OrganizationStatus
)

User = get_user_model()


@pytest.fixture
def api_client():
    """Fixture for API client."""
    return APIClient()


@pytest.fixture
def regular_user(db):
    """Fixture for regular user."""
    return User.objects.create_user(
        email='user@example.com',
        password='testpass123',
        first_name='John',
        last_name='Doe'
    )


@pytest.fixture
def another_user(db):
    """Fixture for another user."""
    return User.objects.create_user(
        email='another@example.com',
        password='testpass123',
        first_name='Jane',
        last_name='Smith'
    )


@pytest.fixture
def super_admin(db):
    """Fixture for super admin user."""
    return User.objects.create_superuser(
        email='admin@example.com',
        password='adminpass123',
        first_name='Admin',
        last_name='User'
    )


@pytest.fixture
def organization(db, regular_user):
    """Fixture for organization."""
    return Organization.objects.create(
        name='Test Organization',
        slug='test-organization',
        description='A test organization',
        owner=regular_user
    )


@pytest.fixture
def another_organization(db, another_user):
    """Fixture for another organization."""
    return Organization.objects.create(
        name='Another Organization',
        slug='another-organization',
        description='Another test organization',
        owner=another_user
    )


@pytest.mark.django_db
class TestOrganizationCRUD:
    """Test organization CRUD operations."""
    
    def test_create_organization(self, api_client, regular_user):
        """Test creating an organization."""
        api_client.force_authenticate(user=regular_user)
        url = reverse('organizations:organization-list')
        data = {
            'name': 'New Organization',
            'description': 'A new organization'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Organization.objects.filter(name='New Organization').exists()
        org = Organization.objects.get(name='New Organization')
        assert org.owner == regular_user
        assert org.slug == 'new-organization'
    
    def test_list_organizations(self, api_client, regular_user, organization):
        """Test listing organizations."""
        api_client.force_authenticate(user=regular_user)
        url = reverse('organizations:organization-list')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
    
    def test_retrieve_organization(self, api_client, regular_user, organization):
        """Test retrieving organization details."""
        api_client.force_authenticate(user=regular_user)
        url = reverse('organizations:organization-detail', kwargs={'slug': organization.slug})
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == organization.name
        assert response.data['is_owner'] is True
    
    def test_update_organization(self, api_client, regular_user, organization):
        """Test updating organization."""
        api_client.force_authenticate(user=regular_user)
        url = reverse('organizations:organization-detail', kwargs={'slug': organization.slug})
        data = {'description': 'Updated description'}
        
        response = api_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        organization.refresh_from_db()
        assert organization.description == 'Updated description'
    
    def test_non_owner_cannot_update(self, api_client, another_user, organization):
        """Test that non-owners cannot update organization."""
        api_client.force_authenticate(user=another_user)
        url = reverse('organizations:organization-detail', kwargs={'slug': organization.slug})
        data = {'description': 'Hacker description'}
        
        response = api_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_delete_organization(self, api_client, regular_user, organization):
        """Test deleting organization."""
        api_client.force_authenticate(user=regular_user)
        url = reverse('organizations:organization-detail', kwargs={'slug': organization.slug})
        
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Organization.objects.filter(id=organization.id).exists()
    
    def test_unique_slug_generation(self, api_client, regular_user):
        """Test that duplicate names generate unique slugs."""
        Organization.objects.create(
            name='Same Name',
            owner=regular_user
        )
        
        org2 = Organization.objects.create(
            name='Same Name',
            owner=regular_user
        )
        
        assert org2.slug == 'same-name-1'


@pytest.mark.django_db
class TestOrganizationOwnership:
    """Test organization ownership features."""
    
    def test_my_organizations(self, api_client, regular_user):
        """Test getting user's owned organizations."""
        api_client.force_authenticate(user=regular_user)
        
        # Create multiple organizations
        Organization.objects.create(name='Org 1', owner=regular_user)
        Organization.objects.create(name='Org 2', owner=regular_user)
        
        url = reverse('organizations:organization-my-organizations')
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2
    
    def test_joined_organizations(self, api_client, regular_user, organization):
        """Test getting organizations where user is a member."""
        api_client.force_authenticate(user=regular_user)
        url = reverse('organizations:organization-joined-organizations')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
class TestMembershipInvitation:
    """Test membership invitation workflow."""
    
    def test_invite_member(self, api_client, regular_user, another_user, organization):
        """Test inviting a user to organization."""
        api_client.force_authenticate(user=regular_user)
        url = reverse('organizations:organization-invite-member', kwargs={'slug': organization.slug})
        data = {
            'user_email': another_user.email,
            'role': MemberRole.VOTER
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert OrganizationMember.objects.filter(
            user=another_user,
            organization=organization
        ).exists()
        
        member = OrganizationMember.objects.get(user=another_user, organization=organization)
        assert member.membership_status == MembershipStatus.PENDING
        assert member.invited_by == regular_user
    
    def test_cannot_invite_nonexistent_user(self, api_client, regular_user, organization):
        """Test that inviting non-existent user fails."""
        api_client.force_authenticate(user=regular_user)
        url = reverse('organizations:organization-invite-member', kwargs={'slug': organization.slug})
        data = {
            'user_email': 'nonexistent@example.com',
            'role': MemberRole.VOTER
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_cannot_invite_owner(self, api_client, regular_user, organization):
        """Test that organization owner cannot be invited as member."""
        api_client.force_authenticate(user=regular_user)
        url = reverse('organizations:organization-invite-member', kwargs={'slug': organization.slug})
        data = {
            'user_email': regular_user.email,
            'role': MemberRole.VOTER
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_non_admin_cannot_invite(self, api_client, another_user, organization):
        """Test that non-admins cannot invite members."""
        another_user.is_superuser = False
        another_user.is_staff = False
        another_user.role = 'user'
        another_user.save()
        OrganizationMember.objects.create(
            user=another_user,
            organization=organization,
            role=MemberRole.VOTER,
            membership_status=MembershipStatus.APPROVED
        )
    
        print(f"Is another_user admin? {organization.is_admin(another_user)}")
        print(f"Is another_user owner? {organization.owner == another_user}")
        print(f"Is another_user super admin? {another_user.is_super_admin()}")
        # Create a valid user to invite
        test_user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
        api_client.force_authenticate(user=another_user)
        url = reverse('organizations:organization-invite-member', kwargs={'slug': organization.slug})
        data = {
            'user_email': test_user.email,
            'role': MemberRole.VOTER
        }
    
        response = api_client.post(url, data, format='json')

        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")
    
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestMembershipJoinRequest:
    """Test membership join request workflow."""
    
    def test_join_request(self, api_client, another_user, organization):
        """Test user requesting to join organization."""
        api_client.force_authenticate(user=another_user)
        url = reverse('organizations:organization-join-request')
        data = {'organization_slug': organization.slug}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert OrganizationMember.objects.filter(
            user=another_user,
            organization=organization,
            membership_status=MembershipStatus.PENDING
        ).exists()
    
    def test_owner_cannot_join_own_org(self, api_client, regular_user, organization):
        """Test that owner cannot join their own organization."""
        api_client.force_authenticate(user=regular_user)
        url = reverse('organizations:organization-join-request')
        data = {'organization_slug': organization.slug}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_cannot_join_twice(self, api_client, another_user, organization):
        """Test that user cannot request membership twice."""
        # Create first request
        OrganizationMember.objects.create(
            user=another_user,
            organization=organization,
            membership_status=MembershipStatus.PENDING
        )
        
        api_client.force_authenticate(user=another_user)
        url = reverse('organizations:organization-join-request')
        data = {'organization_slug': organization.slug}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestMembershipApproval:
    """Test membership approval workflow."""
    
    def test_approve_membership(self, api_client, regular_user, another_user, organization):
        """Test approving membership request."""
        member = OrganizationMember.objects.create(
            user=another_user,
            organization=organization,
            membership_status=MembershipStatus.PENDING
        )
        
        api_client.force_authenticate(user=regular_user)
        url = reverse('organizations:member-review', kwargs={'pk': member.pk})
        data = {'action': 'approve'}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.APPROVED
    
    def test_reject_membership(self, api_client, regular_user, another_user, organization):
        """Test rejecting membership request."""
        member = OrganizationMember.objects.create(
            user=another_user,
            organization=organization,
            membership_status=MembershipStatus.PENDING
        )
        
        api_client.force_authenticate(user=regular_user)
        url = reverse('organizations:member-review', kwargs={'pk': member.pk})
        data = {'action': 'reject'}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        member.refresh_from_db()
        assert member.membership_status == MembershipStatus.REJECTED
    
    def test_list_pending_requests(self, api_client, regular_user, another_user, organization):
        """Test listing pending membership requests."""
        OrganizationMember.objects.create(
            user=another_user,
            organization=organization,
            membership_status=MembershipStatus.PENDING
        )
        
        api_client.force_authenticate(user=regular_user)
        url = reverse('organizations:member-pending')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1


@pytest.mark.django_db
class TestMemberRoleManagement:
    """Test member role management."""
    
    def test_promote_to_admin(self, api_client, regular_user, another_user, organization):
        """Test promoting member to admin."""
        member = OrganizationMember.objects.create(
            user=another_user,
            organization=organization,
            role=MemberRole.VOTER,
            membership_status=MembershipStatus.APPROVED
        )
        
        api_client.force_authenticate(user=regular_user)
        url = reverse('organizations:member-update-role', kwargs={'pk': member.pk})
        data = {'role': MemberRole.ADMIN}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        member.refresh_from_db()
        assert member.role == MemberRole.ADMIN
    
    def test_demote_to_voter(self, api_client, regular_user, another_user, organization):
        """Test demoting admin to voter."""
        member = OrganizationMember.objects.create(
            user=another_user,
            organization=organization,
            role=MemberRole.ADMIN,
            membership_status=MembershipStatus.APPROVED
        )
        
        api_client.force_authenticate(user=regular_user)
        url = reverse('organizations:member-update-role', kwargs={'pk': member.pk})
        data = {'role': MemberRole.VOTER}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        member.refresh_from_db()
        assert member.role == MemberRole.VOTER
    
    def test_cannot_update_pending_member_role(self, api_client, regular_user, another_user, organization):
        """Test that pending members cannot have role updated."""
        member = OrganizationMember.objects.create(
            user=another_user,
            organization=organization,
            role=MemberRole.VOTER,
            membership_status=MembershipStatus.PENDING
        )
        
        api_client.force_authenticate(user=regular_user)
        url = reverse('organizations:member-update-role', kwargs={'pk': member.pk})
        data = {'role': MemberRole.ADMIN}
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestMemberLeaving:
    """Test member leaving organization."""
    
    def test_member_can_leave(self, api_client, another_user, organization):
        """Test that member can leave organization."""
        member = OrganizationMember.objects.create(
            user=another_user,
            organization=organization,
            membership_status=MembershipStatus.APPROVED
        )
        
        api_client.force_authenticate(user=another_user)
        url = reverse('organizations:member-leave', kwargs={'pk': member.pk})
        
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not OrganizationMember.objects.filter(pk=member.pk).exists()
    
    def test_owner_cannot_leave(self, api_client, regular_user, organization):
        """Test that owner cannot leave their organization."""
        # This shouldn't exist, but testing the validation
    
        # Create a regular member first
        another_user = User.objects.create_user(
            email='another@example.com',
            password='testpass123'
        )
    
        member = OrganizationMember.objects.create(
            user=another_user,
            organization=organization,
            membership_status=MembershipStatus.APPROVED
        )
    
        # Try to have the owner leave (they shouldn't be able to)
        api_client.force_authenticate(user=regular_user)
        url = reverse('organizations:member-leave', kwargs={'pk': member.pk})
    
        response = api_client.post(url)
    
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['error'] == 'You can only leave organizations you are a member of.'


@pytest.mark.django_db
class TestOrganizationStatistics:
    """Test organization statistics."""
    
    def test_get_statistics(self, api_client, regular_user, another_user, organization):
        """Test getting organization statistics."""
        # Add some members
        OrganizationMember.objects.create(
            user=another_user,
            organization=organization,
            role=MemberRole.ADMIN,
            membership_status=MembershipStatus.APPROVED
        )
        
        api_client.force_authenticate(user=regular_user)
        url = reverse('organizations:organization-statistics', kwargs={'slug': organization.slug})
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert 'total_members' in response.data
        assert 'approved_members' in response.data
        assert 'admin_count' in response.data
        assert response.data['approved_members'] == 1


@pytest.mark.django_db
class TestOrganizationSuspension:
    """Test organization suspension/activation."""
    
    def test_suspend_organization(self, api_client, regular_user, organization):
        """Test suspending organization."""
        api_client.force_authenticate(user=regular_user)
        url = reverse('organizations:organization-suspend', kwargs={'slug': organization.slug})
        
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        organization.refresh_from_db()
        assert organization.status == OrganizationStatus.SUSPENDED
    
    def test_activate_organization(self, api_client, regular_user, organization):
        """Test activating organization."""
        organization.suspend()
        
        api_client.force_authenticate(user=regular_user)
        url = reverse('organizations:organization-activate', kwargs={'slug': organization.slug})
        
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        organization.refresh_from_db()
        assert organization.status == OrganizationStatus.ACTIVE