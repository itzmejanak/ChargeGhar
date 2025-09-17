#!/bin/bash

# PowerBank Django Fixtures Loader Script
# Loads all fixtures in proper dependency order

set -e  # Exit on any error

echo "🚀 Starting PowerBank Fixtures Loading..."
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if we're in the correct directory
if [[ ! -f "manage.py" ]]; then
    print_error "manage.py not found! Please run this script from the Django project root directory."
    exit 1
fi

# Find the correct API container
API_CONTAINER=$(docker ps --format "{{.Names}}" | grep "powerbank.*api" | head -1)
if [[ -z "$API_CONTAINER" ]]; then
    print_error "No PowerBank API container is running!"
    echo "Available containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}" | grep powerbank || echo "No PowerBank containers found"
    exit 1
fi

print_status "Using API container: $API_CONTAINER"

print_status "Docker containers are running ✓"

# Wait for API to be ready
print_status "Waiting for API to be ready..."
sleep 10

# Function to create superuser if it doesn't exist
create_superuser() {
    print_step "Creating superuser..."
    
    # Check if superuser already exists
    if docker exec -i "$API_CONTAINER" python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if User.objects.filter(is_superuser=True).exists():
    print('Superuser already exists')
    exit()
else:
    print('No superuser found')
    exit(1)
" 2>/dev/null; then
        print_status "Superuser already exists ✓"
    else
        print_status "Creating superuser..."
        docker exec -i "$API_CONTAINER" python manage.py shell -c "
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
    print(f'User {username} already exists')
"
        print_status "✓ Superuser created successfully"
    fi
}

# Function to load fixtures for an app
load_fixtures() {
    local app_name=$1
    local fixtures_dir="api/$app_name/fixtures"

    if [[ -d "$fixtures_dir" ]]; then
        print_step "Loading fixtures for $app_name..."

        # Find all .json files in the fixtures directory
        local fixtures=$(find "$fixtures_dir" -name "*.json" -type f | sort)

        if [[ -z "$fixtures" ]]; then
            print_warning "No fixtures found in $fixtures_dir"
            return
        fi

        # Load each fixture file
        for fixture in $fixtures; do
            local fixture_name=$(basename "$fixture")
            print_status "Loading $fixture_name..."

            # Use the correct API container to run the loaddata command
            if docker exec -i "$API_CONTAINER" python manage.py loaddata "$fixture" 2>/dev/null; then
                print_status "✓ Successfully loaded $fixture_name"
            else
                print_warning "⚠ Failed to load $fixture_name (might already exist or have dependencies)"
            fi
        done
    else
        print_warning "Fixtures directory not found: $fixtures_dir"
    fi
}

# Create superuser first
create_superuser

# Load fixtures in dependency order
print_step "Loading fixtures in dependency order..."
echo ""

# 1. Config - Basic app configuration
load_fixtures "config"

# 2. Users - Foundational user data
load_fixtures "users"

# 3. Content - Static content data
load_fixtures "content"

# 4. Stations - Station, amenity, slot, and power bank data
load_fixtures "stations"

# 5. Rentals - Rental packages and rental data (depends on users, stations)
load_fixtures "rentals"

# 6. Payments - Payment methods, wallets, transactions (depends on users, rentals)
load_fixtures "payments"

# 7. Points - User points system (depends on users)
load_fixtures "points"

# 8. Promotions - Promotion data
load_fixtures "promotions"

# 9. Social - Social features (depends on users)
load_fixtures "social"

# 10. Notifications - Notification system (depends on users)
load_fixtures "notifications"

echo ""
print_status "🎉 Fixtures loading completed!"
print_status "========================================="

# Get API port from .env
API_PORT=$(grep "API_PORT" .env | cut -d '=' -f2 | tr -d ' ')
SERVER_IP=$(hostname -I | awk '{print $1}')

print_status "Summary:"
print_status "- Superuser created (check .env for credentials)"
print_status "- Config fixtures loaded"
print_status "- User fixtures loaded"
print_status "- Content fixtures loaded"
print_status "- Station fixtures loaded (stations, amenities, slots, power banks)"
print_status "- Rental fixtures loaded (packages and rentals)"
print_status "- Payment fixtures loaded (methods, wallets, transactions)"
print_status "- Points fixtures loaded"
print_status "- Promotions fixtures loaded"
print_status "- Social fixtures loaded"
print_status "- Notifications fixtures loaded"
echo ""
print_status "🌐 Your PowerBank API is ready!"
print_status "API Base URL: http://$SERVER_IP:${API_PORT:-8010}"
print_status "API Documentation: http://$SERVER_IP:${API_PORT:-8010}/docs/"
print_status "Admin Panel: http://$SERVER_IP:${API_PORT:-8010}/admin/"
print_status "Health Check: http://$SERVER_IP:${API_PORT:-8010}/api/app/health/"
echo ""
print_status "🔧 Useful commands:"
print_status "Django shell: docker-compose -f $DOCKER_COMPOSE_FILE exec powerbank_api python manage.py shell"
print_status "View logs: docker-compose -f $DOCKER_COMPOSE_FILE logs -f powerbank_api"
print_status "Restart API: docker-compose -f $DOCKER_COMPOSE_FILE restart powerbank_api"