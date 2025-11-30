#!/usr/bin/env python
"""
Celery worker script for PythonAnywhere
"""
import os
import sys

# Add project to Python path
project_path = '/home/yourusername/alx-project-nexus/pollr_backend'
if project_path not in sys.path:
    sys.path.insert(0, project_path)

# Change to project directory
os.chdir(project_path)

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pollr_backend.settings')

# Import and start Celery
from pollr_backend.background_tasks.celery import app

if __name__ == '__main__':
    app.start(['worker', '--loglevel=info'])
