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

def get_correct_api_container():
    """Get the correct running API container name"""
    # Check for production container first
    result = subprocess.run('docker ps --format "{{.Names}}" | grep "powerbank.*api"', shell=True, capture_output=True, text=True)
    containers = [c.strip() for c in result.stdout.strip().split('\n') if c.strip()]
    
    # Prefer production container
    for container in containers:
        if 'production' in container:
            return container
    
    # Fall back to any API container
    return containers[0] if containers else None

def run_django_command(command):
    """Run Django management command in container"""
    container_name = get_correct_api_container()
    if not container_name:
        return "", "No API container found"
    
    print(f"Using container: {container_name}")
    full_command = f'docker exec -i {container_name} python manage.py shell -c "{command}"'
    try:
        result = subprocess.run(full_command, shell=True, capture_output=True, text=True, cwd="/opt/powerbank")
        return result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return "", str(e)

def load_fixture_to_container(fixture_path):
    """Load a specific fixture to the correct container"""
    container_name = get_correct_api_container()
    if not container_name:
        return False, "No API container found"
    
    command = f'docker exec -i {container_name} python manage.py loaddata {fixture_path}'
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd="/opt/powerbank")
        return result.returncode == 0, result.stdout + result.stderr
    except Exception as e:
        return False, str(e)

def check_containers():
    """Check container status"""
    print(f"{Colors.BLUE}🐳 Container Status{Colors.ENDC}")
    print("=" * 50)
    
    # Show all PowerBank containers
    result = subprocess.run('docker ps | grep powerbank', shell=True, capture_output=True, text=True, cwd="/opt/powerbank")
    print("PowerBank Containers:")
    print(result.stdout)
    
    # Check if API container is running
    container_name = get_correct_api_container()
    if container_name:
        print(f"{Colors.GREEN}✅ Using API container: {container_name}{Colors.ENDC}")
        return True
    else:
        print(f"{Colors.RED}❌ No PowerBank API container found!{Colors.ENDC}")
        return False

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
    """Reload fixtures to correct container"""
    print(f"\n{Colors.BLUE}🔄 Loading Fixtures to Correct Container{Colors.ENDC}")
    print("=" * 50)
    
    container_name = get_correct_api_container()
    if not container_name:
        print(f"{Colors.RED}❌ No API container found{Colors.ENDC}")
        return
    
    print(f"Loading fixtures to: {container_name}")
    
    confirm = input(f"{Colors.YELLOW}Do you want to load fixtures? (y/N): {Colors.ENDC}")
    if confirm.lower() == 'y':
        fixtures = [
            "api/config/fixtures/config.json",
            "api/users/fixtures/users.json", 
            "api/content/fixtures/content.json",
            "api/stations/fixtures/stations.json",
            "api/rentals/fixtures/rentals.json",
            "api/payments/fixtures/payments.json",
            "api/points/fixtures/points.json",
            "api/promotions/fixtures/promotions.json",
            "api/social/fixtures/social.json",
            "api/notifications/fixtures/notifications.json"
        ]
        
        loaded_count = 0
        for fixture in fixtures:
            if os.path.exists(fixture):
                print(f"Loading {fixture}...")
                success, output = load_fixture_to_container(fixture)
                if success:
                    print(f"{Colors.GREEN}✅ Loaded {fixture}{Colors.ENDC}")
                    loaded_count += 1
                else:
                    print(f"{Colors.YELLOW}⚠ Failed to load {fixture}: {output}{Colors.ENDC}")
            else:
                print(f"{Colors.YELLOW}⚠ Fixture not found: {fixture}{Colors.ENDC}")
        
        print(f"\n{Colors.GREEN}✅ Loaded {loaded_count} fixtures successfully{Colors.ENDC}")
        
        # Create superuser if needed
        print(f"\n{Colors.BLUE}Creating superuser...{Colors.ENDC}")
        create_superuser_cmd = f"""
from django.contrib.auth import get_user_model
import os
User = get_user_model()
username = 'janak'
email = 'janak@powerbank.com'
password = '5060'
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print(f'Superuser {username} created successfully')
else:
    print(f'Superuser {username} already exists')
"""
        stdout, stderr = run_django_command(create_superuser_cmd)
        print(stdout)
        if stderr:
            print(f"{Colors.YELLOW}Note: {stderr}{Colors.ENDC}")

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