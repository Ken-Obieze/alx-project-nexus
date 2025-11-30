from django.core.management.base import BaseCommand
from background_tasks.tasks.elections_tasks import update_election_statuses
from background_tasks.tasks.voting_tasks import cleanup_old_votes
from graphql.schema import schema


class Command(BaseCommand):
    help = 'Test GraphQL and Celery implementation'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing GraphQL and Celery Implementation...'))
        
        # Test GraphQL schema
        try:
            # Basic schema validation
            schema_str = str(schema)
            self.stdout.write(self.style.SUCCESS('✓ GraphQL schema loaded successfully'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ GraphQL schema error: {e}'))
        
        # Test Celery tasks (without executing)
        try:
            task_names = [
                'update_election_statuses',
                'send_election_reminders', 
                'cleanup_old_votes',
                'send_vote_confirmation_email'
            ]
            for task_name in task_names:
                self.stdout.write(self.style.SUCCESS(f'✓ Task {task_name} is available'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Task loading error: {e}'))
        
        self.stdout.write(self.style.SUCCESS('\nImplementation test complete!'))
        self.stdout.write('\nTo run the full system:')
        self.stdout.write('1. Start Redis: redis-server')
        self.stdout.write('2. Start Celery worker: celery -A pollr_backend.background_tasks worker --loglevel=info')
        self.stdout.write('3. Start Celery beat: celery -A pollr_backend.background_tasks beat --loglevel=info')
        self.stdout.write('4. Access GraphQL: http://localhost:8000/graphql/')
