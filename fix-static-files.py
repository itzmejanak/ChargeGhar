#!/usr/bin/env python3
"""
Quick fix for static files serving
"""

import subprocess
import os

def fix_static_files():
    """Fix static files configuration and collection"""
    
    print("🔧 Fixing Static Files Configuration...")
    
    # Find the correct API container
    result = subprocess.run('docker ps --format "{{.Names}}" | grep "powerbank.*api"', 
                          shell=True, capture_output=True, text=True)
    containers = [c.strip() for c in result.stdout.strip().split('\n') if c.strip()]
    
    if not containers:
        print("❌ No PowerBank API container found!")
        return
    
    container = containers[0]
    print(f"✅ Using container: {container}")
    
    # Collect static files
    print("📦 Collecting static files...")
    cmd = f'docker exec -i {container} python manage.py collectstatic --noinput -v 2'
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode == 0:
        print("✅ Static files collected successfully!")
    else:
        print("❌ Failed to collect static files")
        return
    
    # Test static file access
    print("🧪 Testing static file access...")
    test_urls = [
        "https://main.chargeghar.com/static/admin/css/base.css",
        "https://main.chargeghar.com/static/rest_framework/css/bootstrap.min.css"
    ]
    
    for url in test_urls:
        result = subprocess.run(f'curl -I {url}', shell=True, capture_output=True, text=True)
        if "200 OK" in result.stdout:
            print(f"✅ {url} - OK")
        else:
            print(f"❌ {url} - Failed")
    
    print("🎉 Static files fix completed!")

if __name__ == "__main__":
    fix_static_files()