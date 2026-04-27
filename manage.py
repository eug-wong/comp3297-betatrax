#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

def main():
# 加入這兩行
    #from betatrax import settings
    #print(f"DEBUG: INSTALLED_APPS = {settings.INSTALLED_APPS}")    """Run administrative tasks."""
    # 這裡指定了你的 settings 檔案路徑
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'betatrax.settings')
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