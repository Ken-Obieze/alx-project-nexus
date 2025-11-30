#!/usr/bin/env python3
"""
PythonAnywhere deployment script for PollR
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'='*50}")
    print(f"🔄 {description}")
    print(f"{'='*50}")
    print(f"Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ Success: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e.stderr}")
        return False

def setup_pythonanywhere():
    """Setup PollR on PythonAnywhere"""
    
    # Configuration
    PROJECT_NAME = "pollr_backend"
    PYTHON_VERSION = "3.11"
    DOMAIN = "yourusername.pythonanywhere.com"  # Update this
    
    print("🚀 PollR PythonAnywhere Deployment Setup")
    print("=" * 50)
    
    # Step 1: Create virtual environment
    if not run_command(f"mkvirtualenv --python=/usr/bin/python{PYTHON_VERSION} {PROJECT_NAME}", 
                     "Creating virtual environment"):
        return False
    
    # Step 2: Install dependencies
    if not run_command(f"pip install -r requirements-prod.txt", 
                     "Installing production dependencies"):
        return False
    
    # Step 3: Setup environment variables
    env_file = Path(".env")
    if env_file.exists():
        print(f"\n📝 Environment file found at {env_file}")
        print("Please ensure it contains:")
        print("""
DATABASE_NAME=pollrdb
DATABASE_USER=your_db_user
DATABASE_PASSWORD=your_db_password
DATABASE_HOST=your_db_host
DATABASE_PORT=5432
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourusername.pythonanywhere.com,www.yourusername.pythonanywhere.com
REDIS_CLOUD_HOST=your-redis-cloud-host
REDIS_CLOUD_PORT=12345
REDIS_CLOUD_PASSWORD=your-redis-password
REDIS_CLOUD_SSL=True
CELERY_BROKER_URL=rediss://:your-redis-password@your-redis-host:12345/0
CELERY_RESULT_BACKEND=rediss://:your-redis-password@your-redis-host:12345/0
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@pollr.com
        """)
    
    # Step 4: Run migrations
    if not run_command("python manage.py migrate", "Running database migrations"):
        return False
    
    # Step 5: Collect static files
    if not run_command("python manage.py collectstatic --noinput", "Collecting static files"):
        return False
    
    # Step 6: Create superuser (optional)
    print(f"\n👤 Create superuser:")
    print("Run: python manage.py createsuperuser")
    
    print(f"\n✅ Deployment setup complete!")
    print(f"\nNext steps:")
    print(f"1. Update your WSGI file at: /var/www/{DOMAIN}_wsgi.py")
    print(f"2. Setup web app in PythonAnywhere dashboard")
    print(f"3. Configure scheduled tasks for Celery")
    print(f"4. Test your application")
    
    return True

if __name__ == "__main__":
    setup_pythonanywhere()
