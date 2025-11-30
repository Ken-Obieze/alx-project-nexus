"""
Sample Data Population Script for PollR Presentation
Run: python manage.py shell < pollr_backend/script/populate_sample_data.py
"""

from django.contrib.auth import get_user_model
from organizations.models import Organization, OrganizationMember, MembershipStatus, MemberRole
from elections.models import Election, Position, Candidate, ElectionStatus
from voting.models import Vote
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

print(" Starting PollR Sample Data Population...")
print("=" * 60)

# Clear existing data (optional - be careful!)
print("\n Clearing existing data...")
Vote.objects.all().delete()
Candidate.objects.all().delete()
Position.objects.all().delete()
Election.objects.all().delete()
OrganizationMember.objects.all().delete()
Organization.objects.all().delete()
User.objects.filter(is_superuser=False).delete()

print(" Cleared existing data\n")

# ===== USERS =====
print("👥 Creating Users...")

# Admin user
admin = User.objects.create_superuser(
    email='admin@pollr.com',
    password='admin123',
    first_name='Admin',
    last_name='User'
)
print(f"✓ Super Admin: {admin.email} / admin123")

# Organization owners
john = User.objects.create_user(
    email='john@techcorp.com',
    password='john123',
    first_name='John',
    last_name='Doe'
)
print(f"✓ Org Owner: {john.email} / john123")

sarah = User.objects.create_user(
    email='sarah@university.edu',
    password='sarah123',
    first_name='Sarah',
    last_name='Johnson'
)
print(f"✓ Org Owner: {sarah.email} / sarah123")

# Regular members
alice = User.objects.create_user(
    email='alice@techcorp.com',
    password='alice123',
    first_name='Alice',
    last_name='Smith'
)
print(f"✓ Member: {alice.email} / alice123")

bob = User.objects.create_user(
    email='bob@techcorp.com',
    password='bob123',
    first_name='Bob',
    last_name='Williams'
)
print(f"✓ Member: {bob.email} / bob123")

carol = User.objects.create_user(
    email='carol@techcorp.com',
    password='carol123',
    first_name='Carol',
    last_name='Brown'
)
print(f"✓ Member: {carol.email} / carol123")

# University members
david = User.objects.create_user(
    email='david@university.edu',
    password='david123',
    first_name='David',
    last_name='Lee'
)
print(f"✓ Member: {david.email} / david123")

emma = User.objects.create_user(
    email='emma@university.edu',
    password='emma123',
    first_name='Emma',
    last_name='Wilson'
)
print(f"✓ Member: {emma.email} / emma123")

frank = User.objects.create_user(
    email='frank@university.edu',
    password='frank123',
    first_name='Frank',
    last_name='Martinez'
)
print(f"✓ Member: {frank.email} / frank123")

print(f"\n Created {User.objects.count()} users")

# ===== ORGANIZATIONS =====
print("\n Creating Organizations...")

techcorp = Organization.objects.create(
    name='TechCorp Inc.',
    slug='techcorp',
    description='Leading technology company with innovative solutions',
    owner=john,
    status='active'
)
print(f"✓ Organization: {techcorp.name}")

university = Organization.objects.create(
    name='State University',
    slug='state-university',
    description='Premier educational institution',
    owner=sarah,
    status='active'
)
print(f"✓ Organization: {university.name}")

print(f"\n Created {Organization.objects.count()} organizations")

# ===== ORGANIZATION MEMBERS =====
print("\n Adding Organization Members...")

# TechCorp members
member1 = OrganizationMember.objects.create(
    user=alice,
    organization=techcorp,
    role=MemberRole.ADMIN,
    membership_status=MembershipStatus.APPROVED,
    invited_by=john
)
print(f"✓ {alice.get_full_name() or alice.email} → {techcorp.name} (Admin)")

member2 = OrganizationMember.objects.create(
    user=bob,
    organization=techcorp,
    role=MemberRole.VOTER,
    membership_status=MembershipStatus.APPROVED,
    invited_by=john
)
print(f"✓ {bob.get_full_name() or bob.email} → {techcorp.name} (Voter)")

member3 = OrganizationMember.objects.create(
    user=carol,
    organization=techcorp,
    role=MemberRole.VOTER,
    membership_status=MembershipStatus.APPROVED,
    invited_by=alice
)
print(f"✓ {carol.get_full_name() or carol.email} → {techcorp.name} (Voter)")

# Pending member
member4 = OrganizationMember.objects.create(
    user=david,
    organization=techcorp,
    role=MemberRole.VOTER,
    membership_status=MembershipStatus.PENDING
)
print(f"✓ {david.get_full_name() or david.email} → {techcorp.name} (Pending)")

# University members
member5 = OrganizationMember.objects.create(
    user=david,
    organization=university,
    role=MemberRole.ADMIN,
    membership_status=MembershipStatus.APPROVED,
    invited_by=sarah
)
print(f"✓ {david.get_full_name() or david.email} → {university.name} (Admin)")

member6 = OrganizationMember.objects.create(
    user=emma,
    organization=university,
    role=MemberRole.VOTER,
    membership_status=MembershipStatus.APPROVED,
    invited_by=sarah
)
print(f"✓ {emma.get_full_name() or emma.email} → {university.name} (Voter)")

member7 = OrganizationMember.objects.create(
    user=frank,
    organization=university,
    role=MemberRole.VOTER,
    membership_status=MembershipStatus.APPROVED,
    invited_by=david
)
print(f"✓ {frank.get_full_name() or frank.email} → {university.name} (Voter)")

print(f"\n Created {OrganizationMember.objects.count()} memberships")

# ===== ELECTIONS =====
print("\n  Creating Elections...")

# Election 1: Completed election with results
now = timezone.now()
completed_election = Election.objects.create(
    organization=techcorp,
    title='2024 Q1 Board Elections',
    description='Quarterly board member elections for TechCorp Inc.',
    start_at=now - timedelta(days=10),
    end_at=now - timedelta(days=3),
    status=ElectionStatus.COMPLETED,
    result_visibility='public'
)
print(f"✓ Election: {completed_election.title} (Completed)")

# Positions for completed election
president_pos = Position.objects.create(
    election=completed_election,
    title='President',
    description='Lead the organization and set strategic direction',
    order_index=1
)

vp_pos = Position.objects.create(
    election=completed_election,
    title='Vice President',
    description='Support the President and oversee operations',
    order_index=2
)

treasurer_pos = Position.objects.create(
    election=completed_election,
    title='Treasurer',
    description='Manage financial resources and budgets',
    order_index=3
)

print(f"  ✓ Added {completed_election.positions.count()} positions")

# Candidates for President
pres_candidate1 = Candidate.objects.create(
    position=president_pos,
    user=alice,
    name=alice.get_full_name() or alice.email,
    manifesto='Leading with innovation and transparency. My vision is to drive TechCorp to new heights through strategic partnerships and cutting-edge technology adoption.'
)

pres_candidate2 = Candidate.objects.create(
    position=president_pos,
    user=bob,
    name=bob.get_full_name() or bob.email,
    manifesto='Experience meets dedication. I bring 10 years of leadership experience and a proven track record of delivering results.'
)

# Candidates for VP
vp_candidate1 = Candidate.objects.create(
    position=vp_pos,
    user=carol,
    name=carol.get_full_name() or carol.email,
    manifesto='Collaborative leadership for sustainable growth. Together, we can build a stronger organization.'
)

vp_candidate2 = Candidate.objects.create(
    position=vp_pos,
    name='Michael Chen',
    manifesto='External expertise with fresh perspectives. Ready to bring industry best practices to TechCorp.'
)

# Candidates for Treasurer
treasurer_candidate1 = Candidate.objects.create(
    position=treasurer_pos,
    user=bob,
    name=bob.get_full_name() or bob.email,
    manifesto='Financial stability through smart planning. I will ensure every dollar is invested wisely.'
)

treasurer_candidate2 = Candidate.objects.create(
    position=treasurer_pos,
    name='Lisa Wang',
    manifesto='CPA with 15 years experience in financial management. Trust me with your finances.'
)

print(f"  ✓ Added {completed_election.positions.first().election.positions.aggregate(total=__import__('django.db.models').Count('candidates'))['total']} candidates")

# Cast votes for completed election
Vote.objects.create(
    election=completed_election,
    position=president_pos,
    candidate=pres_candidate1,
    voter=member1  # Alice votes
)

Vote.objects.create(
    election=completed_election,
    position=president_pos,
    candidate=pres_candidate1,
    voter=member1  # Alice
)

Vote.objects.create(
    election=completed_election,
    position=president_pos,
    candidate=pres_candidate2,
    voter=member2  # Bob
)

Vote.objects.create(
    election=completed_election,
    position=president_pos,
    candidate=pres_candidate1,
    voter=member3  # Carol
)

Vote.objects.create(
    election=completed_election,
    position=vp_pos,
    candidate=vp_candidate1,
    voter=member1  # Alice
)

Vote.objects.create(
    election=completed_election,
    position=vp_pos,
    candidate=vp_candidate2,
    voter=member1  # Alice
)

Vote.objects.create(
    election=completed_election,
    position=vp_pos,
    candidate=vp_candidate1,
    voter=member2  # Bob
)

Vote.objects.create(
    election=completed_election,
    position=vp_pos,
    candidate=vp_candidate1,
    voter=member3  # Carol
)

Vote.objects.create(
    election=completed_election,
    position=treasurer_pos,
    candidate=treasurer_candidate2,
    voter=member1  # Alice
)

Vote.objects.create(
    election=completed_election,
    position=treasurer_pos,
    candidate=treasurer_candidate2,
    voter=member1  # Alice
)

Vote.objects.create(
    election=completed_election,
    position=treasurer_pos,
    candidate=treasurer_candidate1,
    voter=member2  # Bob
)

Vote.objects.create(
    election=completed_election,
    position=treasurer_pos,
    candidate=treasurer_candidate2,
    voter=member3  # Carol
)

print(f"  ✓ Cast {completed_election.get_total_votes()} votes")

# Election 2: Active/Ongoing election
active_election = Election.objects.create(
    organization=techcorp,
    title='Tech Innovation Award 2024',
    description='Vote for the most innovative tech project of the year',
    start_at=now - timedelta(hours=2),
    end_at=now + timedelta(days=5),
    status=ElectionStatus.ONGOING,
    result_visibility='public'
)
print(f"✓ Election: {active_election.title} (Active)")

# Position for active election
innovation_pos = Position.objects.create(
    election=active_election,
    title='Most Innovative Project',
    description='Select the project that showcases the best innovation',
    order_index=1
)

# Candidates for innovation award
Candidate.objects.create(
    position=innovation_pos,
    name='AI-Powered Analytics Platform',
    manifesto='Revolutionary machine learning system that predicts market trends with 95% accuracy.'
)

Candidate.objects.create(
    position=innovation_pos,
    name='Green Energy Dashboard',
    manifesto='Real-time monitoring system for sustainable energy consumption across all facilities.'
)

Candidate.objects.create(
    position=innovation_pos,
    name='Remote Collaboration Suite',
    manifesto='Next-gen virtual workspace that makes remote work feel like in-person collaboration.'
)

print(f"  ✓ Added {innovation_pos.candidates.count()} candidates")

# Cast some votes for active election
Vote.objects.create(
    election=active_election,
    position=innovation_pos,
    candidate=innovation_pos.candidates.first(),
    voter=member1  # Alice
)

Vote.objects.create(
    election=active_election,
    position=innovation_pos,
    candidate=innovation_pos.candidates.last(),
    voter=member2  # Bob
)

print(f"  ✓ Cast {active_election.get_total_votes()} votes (ongoing)")

# Election 3: Upcoming election
upcoming_election = Election.objects.create(
    organization=university,
    title='Student Council Elections 2024',
    description='Annual student body leadership elections',
    start_at=now + timedelta(days=2),
    end_at=now + timedelta(days=9),
    status=ElectionStatus.SCHEDULED,
    result_visibility='public'
)
print(f"✓ Election: {upcoming_election.title} (Scheduled)")

# Positions for upcoming election
council_pres_pos = Position.objects.create(
    election=upcoming_election,
    title='Student Council President',
    description='Lead the student body and represent student interests',
    order_index=1
)

council_sec_pos = Position.objects.create(
    election=upcoming_election,
    title='Council Secretary',
    description='Manage council documentation and communications',
    order_index=2
)

# Candidates
Candidate.objects.create(
    position=council_pres_pos,
    user=david,
    name=david.get_full_name() or david.email,
    manifesto='Student voice matters! I will ensure every student is heard and represented.'
)

Candidate.objects.create(
    position=council_pres_pos,
    user=emma,
    name=emma.get_full_name() or emma.email,
    manifesto='Building bridges between students and administration for real change.'
)

Candidate.objects.create(
    position=council_sec_pos,
    user=frank,
    name=frank.get_full_name() or frank.email,
    manifesto='Organized, efficient, and always available. Your council deserves the best.'
)

print(f"  ✓ Added {upcoming_election.positions.count()} positions")
print(f"  ✓ Added 3 candidates")

print(f"\n Created {Election.objects.count()} elections")

# ===== SUMMARY =====
print("\n" + "=" * 60)
print(" Sample Data Population Complete!")
print("=" * 60)
print(f"\n Summary:")
print(f"  • Users: {User.objects.count()}")
print(f"  • Organizations: {Organization.objects.count()}")
print(f"  • Memberships: {OrganizationMember.objects.count()}")
print(f"  • Elections: {Election.objects.count()}")
print(f"  • Positions: {Position.objects.count()}")
print(f"  • Candidates: {Candidate.objects.count()}")
print(f"  • Votes: {Vote.objects.count()}")

print(f"\n Login Credentials:")
print(f"\n  Super Admin:")
print(f"    Email: admin@pollr.com")
print(f"    Password: admin123")
print(f"\n  Organization Owners:")
print(f"    Email: john@techcorp.com | Password: john123")
print(f"    Email: sarah@university.edu | Password: sarah123")
print(f"\n  Members:")
print(f"    Email: alice@techcorp.com | Password: alice123")
print(f"    Email: bob@techcorp.com | Password: bob123")
print(f"    Email: carol@techcorp.com | Password: carol123")
print(f"    Email: david@university.edu | Password: david123")
print(f"    Email: emma@university.edu | Password: emma123")
print(f"    Email: frank@university.edu | Password: frank123")

print(f"\n Quick Stats:")
print(f"  • TechCorp: {techcorp.get_member_count()} members, {techcorp.elections.count()} elections")
print(f"  • University: {university.get_member_count()} members, {university.elections.count()} elections")
print(f"  • Completed Election: {completed_election.get_total_votes()} votes, {completed_election.get_voter_turnout():.1f}% turnout")
print(f"  • Active Election: {active_election.get_total_votes()} votes so far")

print("\n Ready for presentation!")
print("=" * 60)