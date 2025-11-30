import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from .models import Election, Position, Candidate, ElectionStatus
from organizations.models import Organization, OrganizationMember, MembershipStatus

User = get_user_model()


@pytest.fixture
def api_client():
    """Fixture for API client."""
    return APIClient()


@pytest.fixture
def user(db):
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
def organization(db, user):
    """Fixture for organization."""
    return Organization.objects.create(
        name='Test Organization',
        slug='test-organization',
        owner=user
    )


@pytest.fixture
def member(db, another_user, organization):
    """Fixture for organization member."""
    return OrganizationMember.objects.create(
        user=another_user,
        organization=organization,
        role='voter',
        membership_status=MembershipStatus.APPROVED
    )


@pytest.fixture
def election(db, organization):
    """Fixture for election."""
    start = timezone.now() + timedelta(days=1)
    end = start + timedelta(days=7)
    return Election.objects.create(
        organization=organization,
        title='Test Election',
        description='A test election',
        start_at=start,
        end_at=end,
        status=ElectionStatus.SCHEDULED
    )


@pytest.fixture
def active_election(db, organization):
    """Fixture for active election."""
    start = timezone.now() - timedelta(days=1)
    end = timezone.now() + timedelta(days=7)
    return Election.objects.create(
        organization=organization,
        title='Active Election',
        description='An active election',
        start_at=start,
        end_at=end,
        status=ElectionStatus.ONGOING
    )


@pytest.fixture
def position(db, election):
    """Fixture for position."""
    return Position.objects.create(
        election=election,
        title='President',
        description='Presidential position',
        order_index=1
    )


@pytest.fixture
def candidate1(db, position, user):
    """Fixture for first candidate."""
    return Candidate.objects.create(
        position=position,
        user=user,
        name=user.full_name,
        manifesto='Vote for me!'
    )


@pytest.fixture
def candidate2(db, position, another_user):
    """Fixture for second candidate."""
    return Candidate.objects.create(
        position=position,
        user=another_user,
        name=another_user.full_name,
        manifesto='I am the best!'
    )


@pytest.mark.django_db
class TestElectionCRUD:
    """Test election CRUD operations."""
    
    def test_create_election(self, api_client, user, organization):
        """Test creating an election."""
        api_client.force_authenticate(user=user)
        url = reverse('elections:election-list')
        
        start = timezone.now() + timedelta(days=1)
        end = start + timedelta(days=7)
        
        data = {
            'organization': organization.id,
            'title': 'New Election',
            'description': 'A new election',
            'start_at': start.isoformat(),
            'end_at': end.isoformat(),
            'result_visibility': 'public'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Election.objects.filter(title='New Election').exists()
    
    def test_create_election_invalid_dates(self, api_client, user, organization):
        """Test creating election with invalid dates."""
        api_client.force_authenticate(user=user)
        url = reverse('elections:election-list')
        
        start = timezone.now() + timedelta(days=7)
        end = timezone.now() + timedelta(days=1)  # End before start
        
        data = {
            'organization': organization.id,
            'title': 'Invalid Election',
            'start_at': start.isoformat(),
            'end_at': end.isoformat()
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_list_elections(self, api_client, user, election):
        """Test listing elections."""
        api_client.force_authenticate(user=user)
        url = reverse('elections:election-list')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
    
    def test_retrieve_election(self, api_client, user, election):
        """Test retrieving election details."""
        api_client.force_authenticate(user=user)
        url = reverse('elections:election-detail', kwargs={'pk': election.pk})
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == election.title
    
    def test_update_election(self, api_client, user, election):
        """Test updating election."""
        api_client.force_authenticate(user=user)
        url = reverse('elections:election-detail', kwargs={'pk': election.pk})
        data = {'description': 'Updated description'}
        
        response = api_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        election.refresh_from_db()
        assert election.description == 'Updated description'
    
    def test_delete_election(self, api_client, user, election):
        """Test deleting election."""
        api_client.force_authenticate(user=user)
        url = reverse('elections:election-detail', kwargs={'pk': election.pk})
        
        response = api_client.delete(url)
        
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Election.objects.filter(id=election.id).exists()


@pytest.mark.django_db
class TestElectionFilters:
    """Test election filtering."""
    
    def test_get_active_elections(self, api_client, user, active_election):
        """Test getting active elections."""
        api_client.force_authenticate(user=user)
        url = reverse('elections:election-active')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    def test_get_upcoming_elections(self, api_client, user, election):
        """Test getting upcoming elections."""
        api_client.force_authenticate(user=user)
        url = reverse('elections:election-upcoming')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
    
    def test_get_by_organization(self, api_client, user, election, organization):
        """Test getting elections by organization."""
        api_client.force_authenticate(user=user)
        url = reverse('elections:election-by-organization')
        
        response = api_client.get(url, {'organization_slug': organization.slug})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1


@pytest.mark.django_db
class TestElectionControl:
    """Test election start/end controls."""
    
    def test_start_election(self, api_client, user, election):
        """Test manually starting an election."""
        api_client.force_authenticate(user=user)
        url = reverse('elections:election-start', kwargs={'pk': election.pk})
        
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        election.refresh_from_db()
        assert election.status == ElectionStatus.ONGOING
    
    def test_end_election(self, api_client, user, active_election):
        """Test manually ending an election."""
        api_client.force_authenticate(user=user)
        url = reverse('elections:election-end', kwargs={'pk': active_election.pk})
        
        response = api_client.post(url)
        
        assert response.status_code == status.HTTP_200_OK
        active_election.refresh_from_db()
        assert active_election.status == ElectionStatus.COMPLETED


@pytest.mark.django_db
class TestPositionCRUD:
    """Test position CRUD operations."""
    
    def test_create_position(self, api_client, user, election):
        """Test creating a position."""
        api_client.force_authenticate(user=user)
        url = reverse('elections:position-list')
        data = {
            'election': election.id,
            'title': 'Vice President',
            'description': 'VP position',
            'order_index': 2
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Position.objects.filter(title='Vice President').exists()
    
    def test_list_positions(self, api_client, user, position):
        """Test listing positions."""
        api_client.force_authenticate(user=user)
        url = reverse('elections:position-list')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
    
    def test_update_position(self, api_client, user, position):
        """Test updating position."""
        api_client.force_authenticate(user=user)
        url = reverse('elections:position-detail', kwargs={'pk': position.pk})
        data = {'description': 'Updated description'}
        
        response = api_client.patch(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        position.refresh_from_db()
        assert position.description == 'Updated description'


@pytest.mark.django_db
class TestCandidateCRUD:
    """Test candidate CRUD operations."""
    
    def test_create_candidate(self, api_client, user, position):
        """Test creating a candidate."""
        api_client.force_authenticate(user=user)
        url = reverse('elections:candidate-list')
        data = {
            'position': position.id,
            'user': user.id,
            'manifesto': 'Vote for change!'
        }
        
        response = api_client.post(url, data, format='json')
        
        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Candidate.objects.filter(user=user, position=position).exists()
    
    def test_create_external_candidate(self, api_client, user, position):
        """Test creating an external candidate."""
        api_client.force_authenticate(user=user)
        url = reverse('elections:candidate-list')
        data = {
            'position': position.id,
            'name': 'External Candidate',
            'manifesto': 'External manifesto'
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Candidate.objects.filter(name='External Candidate').exists()
    
    def test_list_candidates(self, api_client, user, candidate1):
        """Test listing candidates."""
        api_client.force_authenticate(user=user)
        url = reverse('elections:candidate-list')
        
        response = api_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) >= 1
    
    def test_get_candidates_by_position(self, api_client, user, candidate1, position):
        """Test getting candidates by position."""
        api_client.force_authenticate(user=user)
        url = reverse('elections:candidate-by-position')
        
        response = api_client.get(url, {'position_id': position.id})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1