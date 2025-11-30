from django.core.management.base import BaseCommand
from django.conf import settings
import redis
from celery import Celery


class Command(BaseCommand):
    help = 'Test Redis Cloud connection'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Testing Redis Cloud connection...'))
        
        # Test Redis connection
        try:
            redis_url = settings.CELERY_BROKER_URL
            self.stdout.write(f'Connecting to: {redis_url.split("@")[1] if "@" in redis_url else redis_url}')
            
            # Parse Redis URL
            if redis_url.startswith('redis://'):
                redis_client = redis.from_url(redis_url)
                redis_client.ping()
                self.stdout.write(self.style.SUCCESS('✓ Redis Cloud connection successful'))
                
                # Test set/get
                test_key = 'test_redis_cloud_connection'
                redis_client.set(test_key, 'connection_test', ex=60)
                value = redis_client.get(test_key)
                if value == b'connection_test':
                    self.stdout.write(self.style.SUCCESS('✓ Redis read/write test successful'))
                else:
                    self.stdout.write(self.style.ERROR('✗ Redis read/write test failed'))
                
                redis_client.delete(test_key)
                redis_client.close()
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Redis connection failed: {e}'))
            self.stdout.write(self.style.WARNING('\nTroubleshooting tips:'))
            self.stdout.write('1. Check your Redis Cloud credentials in .env file')
            self.stdout.write('2. Verify the endpoint is accessible from your network')
            self.stdout.write('3. Ensure SSL is properly configured if required')
            self.stdout.write('4. Check if Redis Cloud subscription is active')
            return
        
        # Test Celery connection
        try:
            app = Celery('pollr')
            app.conf.broker_url = settings.CELERY_BROKER_URL
            app.conf.result_backend = settings.CELERY_RESULT_BACKEND
            
            # Test broker connection
            inspect = app.control.inspect()
            stats = inspect.stats()
            
            if stats:
                self.stdout.write(self.style.SUCCESS('✓ Celery broker connection successful'))
            else:
                self.stdout.write(self.style.WARNING('⚠ Celery worker not running (expected if not started)'))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Celery connection test failed: {e}'))
        
        self.stdout.write(self.style.SUCCESS('\nRedis Cloud configuration test complete!'))
        
        # Show current configuration
        self.stdout.write('\nCurrent configuration:')
        self.stdout.write(f'Broker URL: {settings.CELERY_BROKER_URL}')
        self.stdout.write(f'Result Backend: {settings.CELERY_RESULT_BACKEND}')
        self.stdout.write(f'Redis SSL: {getattr(settings, "REDIS_CLOUD_SSL", False)}')
