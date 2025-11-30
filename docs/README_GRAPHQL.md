# GraphQL and Background Tasks Implementation

This document describes the GraphQL API and Celery background tasks implementation for PollR.

## Overview

The implementation includes:
- GraphQL API with queries and mutations for all entities
- Celery background tasks for email notifications and periodic jobs
- Comprehensive test coverage

## GraphQL API

### Endpoint
- URL: `/graphql/`
- GraphQL IDE (GraphiQL) available in development mode

### Schema Structure

#### Types
- **UserType**: User information and authentication
- **OrganizationType**: Organization details with member count
- **OrganizationMemberType**: Organization membership details
- **ElectionType**: Election information with voting status
- **PositionType**: Election positions with candidates
- **CandidateType**: Candidate information with vote counts
- **VoteType**: Vote records

#### Queries
```graphql
# User queries
query {
  me {
    id
    email
    fullName
    role
  }
}

# Organization queries
query {
  organization(slug: "org-slug") {
    id
    name
    slug
    memberCount
  }
  
  allOrganizations {
    edges {
      node {
        id
        name
      }
    }
  }
}

# Election queries
query {
  election(id: 1) {
    id
    title
    status
    canVote
    positions {
      id
      title
      candidates {
        id
        name
      }
    }
  }
  
  activeElections {
    id
    title
    status
  }
}

# Vote queries
query {
  myVotes(electionId: 1) {
    id
    candidate {
      name
    }
    position {
      title
    }
  }
  
  electionResults(electionId: 1) {
    position
    candidate
    votes
  }
}
```

#### Mutations
```graphql
# Create organization
mutation {
  createOrganization(name: "New Org", description: "Description") {
    organization {
      id
      name
      slug
    }
  }
}

# Create election
mutation {
  createElection(
    organizationId: 1
    title: "New Election"
    startAt: "2024-01-01T00:00:00Z"
    endAt: "2024-01-07T00:00:00Z"
  ) {
    election {
      id
      title
    }
  }
}

# Cast vote
mutation {
  castVote(
    electionId: 1
    positionId: 1
    candidateId: 1
  ) {
    vote {
      id
      voteToken
    }
    success
  }
}
```

## Background Tasks (Celery)

### Task Categories

#### Election Tasks (`background_tasks/tasks/elections_tasks.py`)
- `update_election_statuses`: Update election status based on time (every 5 minutes)
- `send_election_reminders`: Send reminders for upcoming/ending elections (daily at 9 AM)
- `send_election_started_notification`: Notify when election starts
- `send_election_ended_notification`: Notify when election ends
- `send_election_starting_soon_email`: Reminder for elections starting soon
- `send_election_ending_soon_email`: Last chance to vote reminder
- `send_election_created_notification`: Notify of new elections

#### Voting Tasks (`background_tasks/tasks/voting_tasks.py`)
- `send_vote_confirmation_email`: Send confirmation after voting
- `cleanup_old_votes`: Clean up old vote data (monthly)
- `generate_vote_statistics`: Generate election statistics
- `send_bulk_vote_confirmation`: Confirm bulk votes
- `notify_non_voters`: Remind members who haven't voted

#### Organization Tasks (`background_tasks/tasks/organizations_tasks.py`)
- `send_membership_invitation_email`: Send organization invitations
- `send_membership_approved_email`: Confirm approved memberships
- `send_membership_rejected_email`: Notify rejected memberships
- `send_role_updated_email`: Notify role changes
- `notify_admins_of_join_request`: Alert admins of new requests

### Configuration

#### Celery Settings (in settings.py)
```python
# Celery Configuration
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
```

#### Email Configuration
```python
# Email Configuration (for background tasks)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@pollr.com')
```

## Running the Services

### 1. Install Dependencies
```bash
pip install -r requirements_new.txt
```

### 2. Start Redis (for Celery)
```bash
redis-server
```

### 3. Run Django Development Server
```bash
python manage.py runserver
```

### 4. Start Celery Worker
```bash
celery -A pollr_backend.background_tasks worker --loglevel=info
```

### 5. Start Celery Beat Scheduler
```bash
celery -A pollr_backend.background_tasks beat --loglevel=info
```

## Testing

### GraphQL Tests
```bash
# Run all GraphQL tests
python manage.py test graphql.tests

# Run specific test
python manage.py test graphql.tests.TestGraphQLQueries.test_me_query
```

### Celery Tests
```bash
# Test a specific task
python manage.py shell
>>> from background_tasks.tasks.elections_tasks import update_election_statuses
>>> result = update_election_statuses.delay()
>>> print(result.get())
```

## Environment Variables

Create a `.env` file in the project root:

```env
# Database
DATABASE_NAME=pollrdb
DATABASE_USER=postgres
DATABASE_PASSWORD=password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@pollr.com

# Django
SECRET_KEY=your-secret-key
DEBUG=True
```

## Security Considerations

1. **GraphQL Authentication**: All mutations require authentication
2. **Permission Checks**: Users can only access organizations they're members of
3. **Vote Validation**: Comprehensive validation prevents duplicate voting
4. **Email Security**: Use app-specific passwords for email services
5. **Redis Security**: Secure Redis instance in production

## Monitoring

### Celery Monitoring
- Use Flower for real-time monitoring: `pip install flower`
- Start with: `celery -A pollr_backend.background_tasks flower`

### Task Monitoring
- Check task results in Django admin
- Monitor Redis queues
- Log task failures and retries

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all `apps.` prefixes are removed from imports
2. **Celery Connection**: Verify Redis is running and accessible
3. **Email Failures**: Check SMTP settings and authentication
4. **GraphQL Errors**: Verify schema imports and Django settings

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

1. **GraphQL Subscriptions**: Real-time election updates
2. **Task Queues**: Separate queues for different task priorities
3. **Email Templates**: HTML email templates with branding
4. **Analytics**: Advanced election analytics dashboard
5. **Notifications**: Push notifications for mobile apps
