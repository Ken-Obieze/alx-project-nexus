import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.contrib.auth import get_user_model
from django.db import models

from users.models import User
from organizations.models import Organization, OrganizationMember
from elections.models import Election, Position, Candidate
from voting.models import Vote

User = get_user_model()


# User Types
class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'role',
            'status', 'created_at', 'updated_at'
        )
        filter_fields = {
            'email': ['exact', 'icontains'],
            'role': ['exact'],
            'status': ['exact'],
        }
        interfaces = (graphene.relay.Node,)


# Organization Types
class OrganizationMemberType(DjangoObjectType):
    class Meta:
        model = OrganizationMember
        fields = (
            'id', 'user', 'organization', 'role',
            'membership_status', 'created_at'
        )
        filter_fields = {
            'role': ['exact'],
            'membership_status': ['exact'],
        }
        interfaces = (graphene.relay.Node,)


class OrganizationType(DjangoObjectType):
    member_count = graphene.Int()
    
    class Meta:
        model = Organization
        fields = (
            'id', 'name', 'slug', 'description', 'owner',
            'status', 'created_at', 'updated_at'
        )
        filter_fields = {
            'name': ['exact', 'icontains'],
            'slug': ['exact'],
            'status': ['exact'],
        }
        interfaces = (graphene.relay.Node,)
    
    def resolve_member_count(self, info):
        return self.get_member_count()


# Election Types
class CandidateType(DjangoObjectType):
    vote_count = graphene.Int()
    
    class Meta:
        model = Candidate
        fields = (
            'id', 'position', 'user', 'name', 'manifesto',
            'photo_url', 'created_at'
        )
        interfaces = (graphene.relay.Node,)
    
    def resolve_vote_count(self, info):
        if self.position.election.status == 'completed':
            return self.get_vote_count()
        return None


class PositionType(DjangoObjectType):
    candidates = graphene.List(CandidateType)
    total_votes = graphene.Int()
    
    class Meta:
        model = Position
        fields = (
            'id', 'election', 'title', 'description',
            'order_index', 'created_at'
        )
        filter_fields = {
            'title': ['exact', 'icontains'],
        }
        interfaces = (graphene.relay.Node,)
    
    def resolve_candidates(self, info):
        return self.candidates.all()
    
    def resolve_total_votes(self, info):
        if self.election.status == 'completed':
            return self.get_total_votes()
        return None


class ElectionType(DjangoObjectType):
    positions = graphene.List(PositionType)
    total_votes = graphene.Int()
    can_vote = graphene.Boolean()
    
    class Meta:
        model = Election
        fields = (
            'id', 'organization', 'title', 'description',
            'start_at', 'end_at', 'status', 'result_visibility',
            'created_at', 'updated_at'
        )
        filter_fields = {
            'title': ['exact', 'icontains'],
            'status': ['exact'],
            'organization': ['exact'],
        }
        interfaces = (graphene.relay.Node,)
    
    def resolve_positions(self, info):
        return self.positions.all()
    
    def resolve_total_votes(self, info):
        return self.get_total_votes()
    
    def resolve_can_vote(self, info):
        return self.can_vote()


# Vote Types
class VoteType(DjangoObjectType):
    class Meta:
        model = Vote
        fields = (
            'id', 'election', 'position', 'candidate',
            'vote_token', 'created_at'
        )
        interfaces = (graphene.relay.Node,)


# Queries
class Query(graphene.ObjectType):
    # User queries
    user = graphene.Field(UserType, id=graphene.Int())
    all_users = DjangoFilterConnectionField(UserType)
    me = graphene.Field(UserType)
    
    # Organization queries
    organization = graphene.Field(OrganizationType, id=graphene.Int(), slug=graphene.String())
    all_organizations = DjangoFilterConnectionField(OrganizationType)
    my_organizations = graphene.List(OrganizationType)
    
    # Election queries
    election = graphene.Field(ElectionType, id=graphene.Int())
    all_elections = DjangoFilterConnectionField(ElectionType)
    active_elections = graphene.List(ElectionType)
    
    # Position queries
    position = graphene.Field(PositionType, id=graphene.Int())
    all_positions = DjangoFilterConnectionField(PositionType)
    
    # Candidate queries
    candidate = graphene.Field(CandidateType, id=graphene.Int())
    all_candidates = graphene.List(CandidateType, position_id=graphene.Int())
    
    # Vote queries
    my_votes = graphene.List(VoteType, election_id=graphene.Int(required=True))
    election_results = graphene.List(
        graphene.JSONString,
        election_id=graphene.Int(required=True)
    )
    
    # User resolvers
    def resolve_user(self, info, id):
        return User.objects.get(pk=id)
    
    def resolve_all_users(self, info, **kwargs):
        user = info.context.user
        if user.is_authenticated and user.is_super_admin():
            return User.objects.all()
        return User.objects.none()
    
    def resolve_me(self, info):
        user = info.context.user
        if user.is_authenticated:
            return user
        return None
    
    # Organization resolvers
    def resolve_organization(self, info, id=None, slug=None):
        if id:
            return Organization.objects.get(pk=id)
        elif slug:
            return Organization.objects.get(slug=slug)
        return None
    
    def resolve_all_organizations(self, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            return Organization.objects.none()
        
        if user.is_super_admin():
            return Organization.objects.all()
        
        return Organization.objects.filter(
            models.Q(owner=user) |
            models.Q(members__user=user, members__membership_status='approved')
        ).distinct()
    
    def resolve_my_organizations(self, info):
        user = info.context.user
        if user.is_authenticated:
            return Organization.objects.filter(owner=user)
        return []
    
    # Election resolvers
    def resolve_election(self, info, id):
        return Election.objects.get(pk=id)
    
    def resolve_all_elections(self, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            return Election.objects.none()
        
        if user.is_super_admin():
            return Election.objects.all()
        
        return Election.objects.filter(
            models.Q(organization__owner=user) |
            models.Q(organization__members__user=user,
                    organization__members__membership_status='approved')
        ).distinct()
    
    def resolve_active_elections(self, info):
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        base_query = Election.objects.filter(status='ongoing')
        
        if user.is_super_admin():
            return base_query.all()
        
        return base_query.filter(
            models.Q(organization__owner=user) |
            models.Q(organization__members__user=user,
                    organization__members__membership_status='approved')
        ).distinct()
    
    # Position resolvers
    def resolve_position(self, info, id):
        return Position.objects.get(pk=id)
    
    def resolve_all_positions(self, info, **kwargs):
        return Position.objects.all()
    
    # Candidate resolvers
    def resolve_candidate(self, info, id):
        return Candidate.objects.get(pk=id)
    
    def resolve_all_candidates(self, info, position_id=None):
        if position_id:
            return Candidate.objects.filter(position_id=position_id)
        return Candidate.objects.all()
    
    # Vote resolvers
    def resolve_my_votes(self, info, election_id):
        user = info.context.user
        if not user.is_authenticated:
            return []
        
        return Vote.get_user_votes_for_election(election_id, user)
    
    def resolve_election_results(self, info, election_id):
        user = info.context.user
        election = Election.objects.get(pk=election_id)
        
        if not election.can_view_results(user):
            raise Exception("You don't have permission to view these results")
        
        return Vote.get_results_for_election(election)


# Mutations
class CreateOrganization(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        description = graphene.String()
    
    organization = graphene.Field(OrganizationType)
    
    def mutate(self, info, name, description=None):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception('Authentication required')
        
        organization = Organization.objects.create(
            name=name,
            description=description or '',
            owner=user
        )
        return CreateOrganization(organization=organization)


class CreateElection(graphene.Mutation):
    class Arguments:
        organization_id = graphene.Int(required=True)
        title = graphene.String(required=True)
        description = graphene.String()
        start_at = graphene.DateTime(required=True)
        end_at = graphene.DateTime(required=True)
        result_visibility = graphene.String()
    
    election = graphene.Field(ElectionType)
    
    def mutate(self, info, organization_id, title, start_at, end_at,
               description=None, result_visibility='public'):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception('Authentication required')
        
        organization = Organization.objects.get(pk=organization_id)
        if not organization.can_manage(user):
            raise Exception('Permission denied')
        
        election = Election.objects.create(
            organization=organization,
            title=title,
            description=description or '',
            start_at=start_at,
            end_at=end_at,
            result_visibility=result_visibility
        )
        return CreateElection(election=election)


class CastVote(graphene.Mutation):
    class Arguments:
        election_id = graphene.Int(required=True)
        position_id = graphene.Int(required=True)
        candidate_id = graphene.Int(required=True)
    
    vote = graphene.Field(VoteType)
    success = graphene.Boolean()
    
    def mutate(self, info, election_id, position_id, candidate_id):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception('Authentication required')
        
        election = Election.objects.get(pk=election_id)
        position = Position.objects.get(pk=position_id, election=election)
        candidate = Candidate.objects.get(pk=candidate_id, position=position)
        
        # Check if already voted
        if Vote.has_user_voted_for_position(election, position, user):
            raise Exception('You have already voted for this position')
        
        # Check if election is active
        if not election.can_vote():
            raise Exception('Voting is not currently allowed')
        
        # Create vote
        from organizations.models import OrganizationMember
        
        vote_data = {
            'election': election,
            'position': position,
            'candidate': candidate,
        }
        
        if election.organization.owner == user:
            vote_data['voter_user'] = user
        else:
            member = OrganizationMember.objects.get(
                user=user,
                organization=election.organization,
                membership_status='approved'
            )
            vote_data['voter'] = member
        
        vote = Vote.objects.create(**vote_data)
        return CastVote(vote=vote, success=True)


class Mutation(graphene.ObjectType):
    create_organization = CreateOrganization.Field()
    create_election = CreateElection.Field()
    cast_vote = CastVote.Field()


# Schema
schema = graphene.Schema(query=Query, mutation=Mutation)