import os
from celery import Celery
from celery.schedules import crontab

# Set default Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pollr_backend.settings')

app = Celery('pollr')

# Load config from Django settings with CELERY namespace
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Windows-specific settings
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    # Windows-specific settings
    worker_prefetch_multiplier=1,  # Windows compatibility
    task_acks_late=False,  # Windows compatibility
)

# Celery Beat Schedule for periodic tasks
app.conf.beat_schedule = {
    'update-election-statuses': {
        'task': 'background_tasks.tasks.elections_tasks.update_election_statuses',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'send-election-reminders': {
        'task': 'background_tasks.tasks.elections_tasks.send_election_reminders',
        'schedule': crontab(hour='9', minute='0'),  # Daily at 9 AM
    },
    'cleanup-old-votes': {
        'task': 'background_tasks.tasks.voting_tasks.cleanup_old_votes',
        'schedule': crontab(day_of_month='1', hour='0', minute='0'),  # Monthly
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')