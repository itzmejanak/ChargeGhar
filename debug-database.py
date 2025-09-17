#!/usr/bin/env python3
"""
Debug script to check PowerBank database status
"""

import os
import subprocess
import sys

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def get_api_container_name():
    """Get the actual API container name"""
    result = subprocess.run('docker ps --format "{{.Names}}" | grep api', shell=True, capture_output=True, text=True, cwd="/opt/powerbank")
    containers = result.stdout.strip().split('\n')
    for container in containers:
        if 'api' in container and container.strip():
            return container.strip()
    return None

def run_django_command(command):
    """Run Django management command in container"""
    # Use the actual running container name
    container_name = "powerbank_production-powerbank_api-1"
    full_command = f'docker exec -i {container_name} python manage.py shell -c "{command}"'
    try:
        result = subprocess.run(full_command, shell=True, capture_output=True, text=True, cwd="/opt/powerbank")
        return result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return "", str(e)

def check_containers():
    """Check container status"""
    print(f"{Colors.BLUE}🐳 Container Status{Colors.ENDC}")
    print("=" * 50)
    
    result = subprocess.run('docker-compose -f docker-compose.prod.yml ps', shell=True, capture_output=True, text=True, cwd="/opt/powerbank")
    print(result.stdout)
    
    # Check if API container is running
    api_status = subprocess.run('docker-compose -f docker-compose.prod.yml ps powerbank_api', shell=True, capture_output=True, text=True, cwd="/opt/powerbank")
    if "Up" not in api_status.stdout:
        print(f"{Colors.RED}❌ PowerBank API is not running!{Colors.ENDC}")
        
        # Show API logs
        print(f"\n{Colors.YELLOW}📋 API Container Logs:{Colors.ENDC}")
        logs = subprocess.run('docker-compose -f docker-compose.prod.yml logs --tail=20 powerbank_api', shell=True, capture_output=True, text=True, cwd="/opt/powerbank")
        print(logs.stdout)
        
        return False
    else:
        print(f"{Colors.GREEN}✅ PowerBank API is running{Colors.ENDC}")
        return True

def check_database():
    """Check database tables and data"""
    print(f"{Colors.BLUE}🔍 Checking PowerBank Database Status{Colors.ENDC}")
    print("=" * 50)
    
    # Check users
    command = """
from django.contrib.auth import get_user_model
User = get_user_model()
print(f'Total Users: {User.objects.count()}')
admin_users = User.objects.filter(is_superuser=True)
print(f'Admin Users: {admin_users.count()}')
for user in admin_users:
    print(f'  - {user.username} ({user.email})')
"""
    stdout, stderr = run_django_command(command)
    print(f"{Colors.GREEN}👥 Users:{Colors.ENDC}")
    print(stdout)
    if stderr:
        print(f"{Colors.RED}Error: {stderr}{Colors.ENDC}")
    print()
    
    # Check stations
    command = """
from api.stations.models import Station, StationSlot, PowerBank
print(f'Stations: {Station.objects.count()}')
print(f'Station Slots: {StationSlot.objects.count()}')
print(f'Power Banks: {PowerBank.objects.count()}')
if Station.objects.exists():
    print('Sample stations:')
    for station in Station.objects.all()[:3]:
        print(f'  - {station.station_name} ({station.address})')
"""
    stdout, stderr = run_django_command(command)
    print(f"{Colors.GREEN}🏢 Stations:{Colors.ENDC}")
    print(stdout)
    if stderr:
        print(f"{Colors.RED}Error: {stderr}{Colors.ENDC}")
    print()
    
    # Check config
    command = """
from api.config.models import AppConfig
print(f'App Configs: {AppConfig.objects.count()}')
if AppConfig.objects.exists():
    print('Sample configs:')
    for config in AppConfig.objects.all()[:3]:
        print(f'  - {config.key}: {config.value}')
"""
    stdout, stderr = run_django_command(command)
    print(f"{Colors.GREEN}⚙️ App Config:{Colors.ENDC}")
    print(stdout)
    if stderr:
        print(f"{Colors.RED}Error: {stderr}{Colors.ENDC}")
    print()
    
    # Check all tables
    command = """
from django.apps import apps
total_objects = 0
for model in apps.get_models():
    if hasattr(model, 'objects'):
        count = model.objects.count()
        if count > 0:
            print(f'{model._meta.label}: {count}')
            total_objects += count
print(f'\\nTotal objects in database: {total_objects}')
"""
    stdout, stderr = run_django_command(command)
    print(f"{Colors.GREEN}📊 All Models:{Colors.ENDC}")
    print(stdout)
    if stderr:
        print(f"{Colors.RED}Error: {stderr}{Colors.ENDC}")

def check_admin_access():
    """Check admin panel access"""
    print(f"\n{Colors.BLUE}🔐 Admin Panel Access{Colors.ENDC}")
    print("=" * 50)
    
    # Get admin credentials from .env
    try:
        with open('/opt/powerbank/.env', 'r') as f:
            env_content = f.read()
            
        username = None
        password = None
        for line in env_content.split('\n'):
            if line.startswith('DJANGO_ADMIN_USERNAME='):
                username = line.split('=')[1].strip()
            elif line.startswith('DJANGO_ADMIN_PASSWORD='):
                password = line.split('=')[1].strip()
        
        print(f"{Colors.GREEN}Admin Credentials:{Colors.ENDC}")
        print(f"Username: {username}")
        print(f"Password: {password}")
        print(f"Admin URL: https://main.chargeghar.com/admin/")
        
    except Exception as e:
        print(f"{Colors.RED}Error reading .env: {e}{Colors.ENDC}")

def reload_fixtures():
    """Reload fixtures"""
    print(f"\n{Colors.BLUE}🔄 Reloading Fixtures{Colors.ENDC}")
    print("=" * 50)
    
    confirm = input(f"{Colors.YELLOW}Do you want to reload fixtures? (y/N): {Colors.ENDC}")
    if confirm.lower() == 'y':
        os.chdir('/opt/powerbank')
        result = subprocess.run('./load-fixtures.sh', shell=True)
        if result.returncode == 0:
            print(f"{Colors.GREEN}✅ Fixtures reloaded successfully{Colors.ENDC}")
        else:
            print(f"{Colors.RED}❌ Failed to reload fixtures{Colors.ENDC}")

if __name__ == "__main__":
    if os.geteuid() != 0:
        print(f"{Colors.RED}❌ This script must be run as root{Colors.ENDC}")
        sys.exit(1)
    
    if not os.path.exists("/opt/powerbank"):
        print(f"{Colors.RED}❌ PowerBank project not found at /opt/powerbank{Colors.ENDC}")
        sys.exit(1)
    
    # First check containers
    api_running = check_containers()
    
    if api_running:
        check_database()
        check_admin_access()
        reload_fixtures()
    else:
        print(f"\n{Colors.YELLOW}🔧 API container is not running. Options:{Colors.ENDC}")
        print("1. Restart containers: python3 powerbank-manager.py (option 1)")
        print("2. Check logs: docker-compose -f docker-compose.prod.yml logs powerbank_api")
        print("3. Redeploy: ./deploy-production.sh")