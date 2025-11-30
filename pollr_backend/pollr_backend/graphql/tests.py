import pytest
import json
from django.contrib.auth import get_user_model
from graphene_django.utils.testing import graphql_query
from organizations.models import Organization
from elections.models import Election, Position, Candidate
from datetime import timedelta
from django.utils import timezone

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )


@pytest.fixture
def organization(db, user):
    return Organization.objects.create(
        name='Test Org',
        slug='test-org',
        owner=user
    )


@pytest.fixture
def election(db, organization):
    start = timezone.now() + timedelta(days=1)
    end = start + timedelta(days=7)
    return Election.objects.create(
        organization=organization,
        title='Test Election',
        start_at=start,
        end_at=end
    )


@pytest.mark.django_db
class TestGraphQLQueries:
    """Test GraphQL queries."""
    
    def test_me_query(self, user, client):
        """Test querying current user."""
        client.force_login(user)
        
        query = '''
            query {
                me {
                    id
                    email
                    fullName
                }
            }
        '''
        
        response = graphql_query(query, client=client)
        content = json.loads(response.content)
        
        assert 'errors' not in content
        assert content['data']['me']['email'] == user.email
    
    def test_organization_query(self, user, organization, client):
        """Test querying organization by slug."""
        client.force_login(user)
        
        query = '''
            query {
                organization(slug: "test-org") {
                    id
                    name
                    slug
                    memberCount
                }
            }
        '''
        
        response = graphql_query(query, client=client)
        content = json.loads(response.content)
        
        assert 'errors' not in content
        assert content['data']['organization']['slug'] == 'test-org'
    
    def test_all_organizations_query(self, user, organization, client):
        """Test querying all organizations."""
        client.force_login(user)
        
        query = '''
            query {
                allOrganizations {
                    edges {
                        node {
                            id
                            name
                        }
                    }
                }
            }
        '''
        
        response = graphql_query(query, client=client)
        content = json.loads(response.content)
        
        assert 'errors' not in content
        assert len(content['data']['allOrganizations']['edges']) >= 1
    
    def test_election_query(self, user, election, client):
        """Test querying election."""
        client.force_login(user)
        
        query = f'''
            query {{
                election(id: {election.id}) {{
                    id
                    title
                    status
                    canVote
                }}
            }}
        '''
        
        response = graphql_query(query, client=client)
        content = json.loads(response.content)
        
        assert 'errors' not in content
        assert content['data']['election']['title'] == 'Test Election'
    
    def test_active_elections_query(self, user, client):
        """Test querying active elections."""
        client.force_login(user)
        
        query = '''
            query {
                activeElections {
                    id
                    title
                    status
                }
            }
        '''
        
        response = graphql_query(query, client=client)
        content = json.loads(response.content)
        
        assert 'errors' not in content


@pytest.mark.django_db
class TestGraphQLMutations:
    """Test GraphQL mutations."""
    
    def test_create_organization_mutation(self, user, client):
        """Test creating organization via GraphQL."""
        client.force_login(user)
        
        mutation = '''
            mutation {
                createOrganization(name: "New Org", description: "Test description") {
                    organization {
                        id
                        name
                        slug
                    }
                }
            }
        '''
        
        response = graphql_query(mutation, client=client)
        content = json.loads(response.content)
        
        assert 'errors' not in content
        assert content['data']['createOrganization']['organization']['name'] == 'New Org'
        assert Organization.objects.filter(name='New Org').exists()
    
    def test_create_election_mutation(self, user, organization, client):
        """Test creating election via GraphQL."""
        client.force_login(user)
        
        start = (timezone.now() + timedelta(days=1)).isoformat()
        end = (timezone.now() + timedelta(days=8)).isoformat()
        
        mutation = f'''
            mutation {{
                createElection(
                    organizationId: {organization.id},
                    title: "GraphQL Election",
                    description: "Created via GraphQL",
                    startAt: "{start}",
                    endAt: "{end}"
                ) {{
                    election {{
                        id
                        title
                    }}
                }}
            }}
        '''
        
        response = graphql_query(mutation, client=client)
        content = json.loads(response.content)
        
        assert 'errors' not in content
        assert content['data']['createElection']['election']['title'] == 'GraphQL Election'
    
    def test_unauthorized_mutation(self, client):
        """Test that unauthenticated users cannot create organizations."""
        mutation = '''
            mutation {
                createOrganization(name: "Unauthorized Org") {
                    organization {
                        id
                    }
                }
            }
        '''
        
        response = graphql_query(mutation, client=client)
        content = json.loads(response.content)
        
        assert 'errors' in content