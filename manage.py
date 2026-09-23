#!/usr/bin/env python
"""Convenience root wrapper for Django's command-line utility."""
import os
import sys
from pathlib import Path


def main():
    """Run administrative tasks from root workspace."""
    root_dir = Path(__file__).resolve().parent
    backend_dir = root_dir / 'backend'
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

