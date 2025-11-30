import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model

from .models import Vote
from elections.models import Election, Position, Candidate, ElectionStatus
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
def completed_election(db, organization):
    """Fixture for completed election."""
    start = timezone.now() - timedelta(days=8)
    end = timezone.now() - timedelta(days=1)
    return Election.objects.create(
        organization=organization,
        title='Completed Election',
        description='A completed election',
        start_at=start,
        end_at=end,
        status=ElectionStatus.COMPLETED
    )


@pytest.fixture
def position(db, active_election):
    """Fixture for position."""
    return Position.objects.create(
        election=active_election,
        title='President',
        description='Presidential position',
        order_index=1
    )


@pytest.fixture
def position2(db, active_election):
    """Fixture for second position."""
    return Position.objects.create(
        election=active_election,
        title='Vice President',
        description='VP position',
        order_index=2
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
def candidate2(db, position, user):
    """Fixture for second candidate."""
    return Candidate.objects.create(
        position=position,
        user=user,
        name=user.full_name,
        manifesto='I am the best!'
    )


@pytest.mark.django_db
class TestVoteCasting:
    """Test vote casting functionality."""
    
    def test_cast_vote_as_owner(self, api_client, user, active_election, position, candidate1):
        """Test casting a vote as organization owner."""
        api_client.force_authenticate(user=user)
        url = reverse('voting:vote-cast')
        data = {
            'election_id': active_election.id,
            'position_id': position.id,
            'candidate_id': candidate1.id
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Vote.objects.filter(
            election=active_election,
            position=position,
            candidate=candidate1,
            voter_user=user
        ).exists()
    
    def test_cast_vote_as_member(self, api_client, another_user, member, active_election, position, candidate1):
        """Test casting a vote as organization member."""
        api_client.force_authenticate(user=another_user)
        url = reverse('voting:vote-cast')
        data = {
            'election_id': active_election.id,
            'position_id': position.id,
            'candidate_id': candidate1.id
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert Vote.objects.filter(
            election=active_election,
            position=position,
            candidate=candidate1,
            voter=member
        ).exists()
    
    def test_cannot_vote_twice_same_position(self, api_client, user, active_election, position, candidate1, candidate2):
        """Test that user cannot vote twice for same position."""
        api_client.force_authenticate(user=user)
        url = reverse('voting:vote-cast')
        
        # First vote
        data1 = {
            'election_id': active_election.id,
            'position_id': position.id,
            'candidate_id': candidate1.id
        }
        response1 = api_client.post(url, data1, format='json')
        assert response1.status_code == status.HTTP_201_CREATED
        
        # Second vote for same position
        data2 = {
            'election_id': active_election.id,
            'position_id': position.id,
            'candidate_id': candidate2.id
        }
        response2 = api_client.post(url, data2, format='json')
        assert response2.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_cannot_vote_inactive_election(self, api_client, user, completed_election):
        """Test that users cannot vote in inactive elections."""
        position = Position.objects.create(
            election=completed_election,
            title='President'
        )
        candidate = Candidate.objects.create(
            position=position,
            name='Test Candidate'
        )
        
        api_client.force_authenticate(user=user)
        url = reverse('voting:vote-cast')
        data = {
            'election_id': completed_election.id,
            'position_id': position.id,
            'candidate_id': candidate.id
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_vote_has_unique_token(self, api_client, user, active_election, position, candidate1):
        """Test that each vote has a unique token."""
        api_client.force_authenticate(user=user)
        url = reverse('voting:vote-cast')
        data = {
            'election_id': active_election.id,
            'position_id': position.id,
            'candidate_id': candidate1.id
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'vote_token' in response.data
        assert response.data['vote_token'] is not None


@pytest.mark.django_db
class TestBulkVoting:
    """Test bulk vote casting."""
    
    def test_bulk_vote_cast(self, api_client, user, active_election, position, position2, candidate1):
        """Test casting multiple votes at once."""
        candidate3 = Candidate.objects.create(
            position=position2,
            name='VP Candidate'
        )
        
        api_client.force_authenticate(user=user)
        url = reverse('voting:vote-bulk-cast')
        data = {
            'election_id': active_election.id,
            'votes': [
                {'position_id': position.id, 'candidate_id': candidate1.id},
                {'position_id': position2.id, 'candidate_id': candidate3.id}
            ]
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data) == 2
        assert Vote.objects.filter(election=active_election).count() == 2
    
    def test_bulk_vote_duplicate_position(self, api_client, user, active_election, position, candidate1, candidate2):
        """Test that bulk vote rejects duplicate positions."""
        api_client.force_authenticate(user=user)
        url = reverse('voting:vote-bulk-cast')
        data = {
            'election_id': active_election.id,
            'votes': [
                {'position_id': position.id, 'candidate_id': candidate1.id},
                {'position_id': position.id, 'candidate_id': candidate2.id}
            ]
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
    
    def test_bulk_vote_rollback_on_error(self, api_client, user, active_election, position, position2, candidate1):
        """Test that bulk vote rolls back all votes if one fails."""
        # Cast vote for position 1 first - bypass validation for testing
        vote = Vote(
            election=active_election,
            position=position,
            candidate=candidate1,
            voter_user=user
        )
        vote.save(validate=False)
        
        candidate3 = Candidate.objects.create(
            position=position2,
            name='VP Candidate'
        )
        
        api_client.force_authenticate(user=user)
        url = reverse('voting:vote-bulk-cast')
        data = {
            'election_id': active_election.id,
            'votes': [
                {'position_id': position.id, 'candidate_id': candidate1.id},  # Will fail
                {'position_id': position2.id, 'candidate_id': candidate3.id}
            ]
        }
        
        initial_count = Vote.objects.count()
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # No new votes should be created
        assert Vote.objects.count() == initial_count


@pytest.mark.django_db
class TestVoteResults:
    """Test vote results functionality."""
    
    def test_get_election_results(self, api_client, user, active_election):
        """Test getting election results."""
        position = Position.objects.create(
            election=active_election,
            title='President'
        )
        candidate1 = Candidate.objects.create(
            position=position,
            name='Candidate 1'
        )
        candidate2 = Candidate.objects.create(
            position=position,
            name='Candidate 2'
        )
        
        # Cast some votes - bypass validation for testing
        vote1 = Vote(
            election=active_election,
            position=position,
            candidate=candidate1,
            voter_user=user
        )
        vote1.save(validate=False)
        
        vote2 = Vote(
            election=active_election,
            position=position,
            candidate=candidate1,
            voter_user=user
        )
        vote2.save(validate=False)
        
        vote3 = Vote(
            election=active_election,
            position=position,
            candidate=candidate2,
            voter_user=user
        )
        vote3.save(validate=False)
        
        api_client.force_authenticate(user=user)
        url = reverse('voting:vote-results')
        
        response = api_client.get(url, {'election_id': active_election.id})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 1
        assert response.data[0]['total_votes'] == 3
    
    def test_cannot_view_results_private_ongoing(self, api_client, another_user, active_election):
        """Test that users cannot view private results for ongoing elections."""
        active_election.result_visibility = 'private'
        active_election.save()
        
        api_client.force_authenticate(user=another_user)
        url = reverse('voting:vote-results')
        
        response = api_client.get(url, {'election_id': active_election.id})
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
    
    def test_get_position_results(self, api_client, user, active_election):
        """Test getting position-specific results."""
        position = Position.objects.create(
            election=active_election,
            title='President'
        )
        candidate1 = Candidate.objects.create(
            position=position,
            name='Candidate 1'
        )
        
        # Create vote bypassing validation for testing
        vote = Vote(
            election=active_election,
            position=position,
            candidate=candidate1,
            voter_user=user
        )
        vote.save(validate=False)
        
        api_client.force_authenticate(user=user)
        url = reverse('voting:vote-position-results')
        
        response = api_client.get(url, {'position_id': position.id})
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['total_votes'] == 1
        assert len(response.data['candidates']) >= 1


@pytest.mark.django_db
class TestMyVotes:
    """Test viewing user's own votes."""
    
    def test_get_my_votes(self, api_client, user, active_election, position, candidate1):
        """Test getting user's votes for an election."""
        vote = Vote(
            election=active_election,
            position=position,
            candidate=candidate1,
            voter_user=user
        )
        vote.save(validate=False)
        
        api_client.force_authenticate(user=user)
        url = reverse('voting:vote-my-votes')
        
        response = api_client.get(url, {'election_id': active_election.id})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
    
    def test_cannot_view_others_votes(self, api_client, user, another_user, active_election, position, candidate1):
        """Test that users cannot view other users' votes."""
        vote = Vote(
            election=active_election,
            position=position,
            candidate=candidate1,
            voter_user=another_user
        )
        vote.save(validate=False)
        
        api_client.force_authenticate(user=user)
        url = reverse('voting:vote-my-votes')
        
        response = api_client.get(url, {'election_id': active_election.id})
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 0  # Should not see other user's votes