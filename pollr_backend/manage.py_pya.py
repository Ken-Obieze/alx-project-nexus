#!/usr/bin/env python
"""Django's command-line utility for administrative tasks on PythonAnywhere."""
import os
import sys


def main():
    """Run administrative tasks."""
    # Add project to Python path
    project_path = '/home/yourusername/alx-project-nexus/pollr_backend'
    if project_path not in sys.path:
        sys.path.insert(0, project_path)
    
    # Change to project directory
    os.chdir(project_path)
    
    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pollr_backend.settings')
    
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
