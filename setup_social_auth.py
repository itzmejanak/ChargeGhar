#!/usr/bin/env python
"""
Setup script for Social Authentication (Google & Apple Login)
Run this after updating dependencies and environment variables
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.config.settings')
django.setup()

from django.contrib.sites.models import Site
from django.core.management import execute_from_command_line

def setup_social_auth():
    """Setup social authentication requirements"""
    
    print("🚀 Setting up Social Authentication...")
    
    # 1. Run migrations
    print("\n📦 Running migrations...")
    execute_from_command_line(['manage.py', 'migrate'])
    
    # 2. Create Site object for allauth
    print("\n🌐 Creating Site object...")
    try:
        site, created = Site.objects.get_or_create(
            id=1,
            defaults={
                'domain': 'main.chargeghar.com',
                'name': 'ChargeGhar Nepal'
            }
        )
        if created:
            print(f"✅ Created site: {site.domain}")
        else:
            print(f"✅ Site already exists: {site.domain}")
    except Exception as e:
        print(f"❌ Error creating site: {e}")
    
    # 3. Check environment variables
    print("\n🔐 Checking environment variables...")
    required_vars = [
        'GOOGLE_OAUTH_CLIENT_ID',
        'GOOGLE_OAUTH_CLIENT_SECRET',
        'APPLE_OAUTH_CLIENT_ID',
        'APPLE_OAUTH_TEAM_ID',
        'APPLE_OAUTH_KEY_ID',
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var) or os.getenv(var).startswith('your_'):
            missing_vars.append(var)
    
    if missing_vars:
        print("⚠️  Missing or placeholder environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n📝 Please update your .env file with actual values from:")
        print("   - Google: https://console.cloud.google.com/")
        print("   - Apple: https://developer.apple.com/")
    else:
        print("✅ All environment variables are set")
    
    # 4. Test imports
    print("\n🧪 Testing imports...")
    try:
        from api.users.adapters import CustomSocialAccountAdapter
        print("✅ CustomSocialAccountAdapter imported successfully")
    except ImportError as e:
        print(f"❌ Error importing adapter: {e}")
    
    try:
        from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
        from allauth.socialaccount.providers.apple.views import AppleOAuth2Adapter
        print("✅ Social provider adapters imported successfully")
    except ImportError as e:
        print(f"❌ Error importing provider adapters: {e}")
    
    print("\n🎉 Social Authentication setup complete!")
    print("\n📋 Next steps:")
    print("1. Update environment variables with real OAuth credentials")
    print("2. Test Google OAuth flow: POST /api/auth/google/login")
    print("3. Test Apple OAuth flow: POST /api/auth/apple/login")
    print("4. Configure mobile app integration")

if __name__ == '__main__':
    setup_social_auth()