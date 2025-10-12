#!/usr/bin/env python
"""
Simple fixture loader for Docker container
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.config.settings')
django.setup()

from django.core.management import call_command
from django.contrib.auth import get_user_model

def main():
    print("🚀 Loading fixtures and creating superuser...")
    
    # Create superuser
    User = get_user_model()
    username = 'janak'
    email = 'janak@powerbank.com'
    password = '5060'
    
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email=email, password=password)
        print(f"✅ Superuser '{username}' created successfully")
    else:
        print(f"ℹ️  Superuser '{username}' already exists")
    
    # Load fixtures in order
    apps = ['common', 'config', 'users', 'content', 'stations', 'rentals', 'payments', 'points', 'promotions', 'social', 'notifications']
    
    for app in apps:
        fixtures_dir = f"api/{app}/fixtures"
        if os.path.exists(fixtures_dir):
            print(f"📦 Loading fixtures for {app}...")
            for filename in os.listdir(fixtures_dir):
                if filename.endswith('.json'):
                    try:
                        call_command('loaddata', f"{fixtures_dir}/{filename}", verbosity=0)
                        print(f"  ✅ Loaded {filename}")
                    except Exception as e:
                        print(f"  ⚠️  Failed to load {filename}: {str(e)}")
    
    print("🎉 Fixtures loading completed!")

if __name__ == '__main__':
    main()