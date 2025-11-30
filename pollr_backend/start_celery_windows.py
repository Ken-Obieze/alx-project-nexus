#!/usr/bin/env python
"""
Windows-friendly Celery startup script
"""
import os
import sys
import subprocess

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set environment variables
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pollr_backend.settings')
os.environ.setdefault('FORKED_BY_MULTIPROCESSING', '1')

def start_celery_worker():
    """Start Celery worker with Windows-compatible settings"""
    cmd = [
        'celery',
        '-A', 'pollr_backend.background_tasks',
        'worker',
        '--loglevel=info',
        '--pool=solo',  # Use solo pool for Windows
        '--concurrency=1',  # Single process for Windows
    ]
    
    print("Starting Celery worker (Windows mode)...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nCelery worker stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Error starting Celery worker: {e}")

def start_celery_beat():
    """Start Celery beat scheduler"""
    cmd = [
        'celery',
        '-A', 'pollr_backend.background_tasks',
        'beat',
        '--loglevel=info',
    ]
    
    print("Starting Celery beat scheduler...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nCelery beat stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"Error starting Celery beat: {e}")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'beat':
        start_celery_beat()
    else:
        start_celery_worker()
