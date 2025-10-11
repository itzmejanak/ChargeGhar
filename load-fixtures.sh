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
        print_status "Creating superuser with updated user model..."
        docker exec -i "$API_CONTAINER" python manage.py shell -c "
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid

User = get_user_model()
username = 'janak'
email = 'janak@powerbank.com'
phone_number = '+9779800000000'

# Check if user already exists
if User.objects.filter(username=username).exists():
    print(f'User {username} already exists')
    user = User.objects.get(username=username)
    if not user.is_superuser:
        user.is_superuser = True
        user.is_staff = True
        user.save()
        print(f'Updated {username} to superuser')
else:
    # Create superuser with new user model fields
    user = User.objects.create_user(
        username=username,
        email=email,
        phone_number=phone_number,
        is_superuser=True,
        is_staff=True,
        is_active=True,
        email_verified=True,
        phone_verified=True,
        profile_completed=True,
        kyc_verified=True,
        kyc_status='APPROVED',
        account_status='ACTIVE',
        created_at=timezone.now(),
        updated_at=timezone.now()
    )
    
    # Set password for admin access
    user.set_password('admin123')
    user.save()
    
    print(f'✓ Superuser {username} created successfully')
    print(f'  - Email: {email}')
    print(f'  - Phone: {phone_number}')
    print(f'  - Password: admin123')
    print(f'  - Profile completed: True')
    print(f'  - KYC verified: True')
    print(f'  - Account status: ACTIVE')
"
        print_status "✓ Superuser created successfully with updated user model"
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

# Function to generate admin JWT token
generate_admin_token() {
    print_step "Generating admin JWT token for API testing..."
    
    local token=$(docker exec -i "$API_CONTAINER" python manage.py shell -c "
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
import sys

try:
    User = get_user_model()
    admin_user = User.objects.get(username='janak')
    refresh = RefreshToken.for_user(admin_user)
    print(str(refresh.access_token))
except Exception as e:
    print(f'Error generating token: {e}', file=sys.stderr)
    sys.exit(1)
" 2>/dev/null)
    
    if [[ -n "$token" && "$token" != *"Error"* ]]; then
        print_status "✓ Admin JWT token generated successfully"
        echo ""
        print_status "🎫 Admin JWT Token (for Swagger UI):"
        echo "$token"
        echo ""
        print_status "📋 Copy this token and use it in Swagger UI Authorization header:"
        print_status "Bearer $token"
        echo ""
    else
        print_warning "⚠ Failed to generate admin JWT token"
    fi
}

# Create superuser first
create_superuser

# Load fixtures in dependency order
print_step "Loading fixtures in dependency order..."
echo ""

# 1. Common - Countries, late fee configs, and other foundational data
load_fixtures "common"

# 2. Config - Basic app configuration
load_fixtures "config"

# 3. Users - Foundational user data
load_fixtures "users"

# 4. Content - Static content data
load_fixtures "content"

# 5. Stations - Station, amenity, slot, and power bank data
load_fixtures "stations"

# 6. Rentals - Rental packages and rental data (depends on users, stations)
load_fixtures "rentals"

# 7. Payments - Payment methods, wallets, transactions (depends on users, rentals)
load_fixtures "payments"

# 8. Points - User points system (depends on users)
load_fixtures "points"

# 9. Promotions - Promotion data
load_fixtures "promotions"

# 10. Social - Social features (depends on users)
load_fixtures "social"

# 11. Notifications - Notification system (depends on users)
load_fixtures "notifications"

# 12. Admin Panel - Admin specific data (if exists)
load_fixtures "admin_panel"

# Generate admin JWT token for immediate testing
generate_admin_token

echo ""
print_status "🎉 Fixtures loading completed!"
print_status "========================================="

# Get API port from .env
API_PORT=$(grep "API_PORT" .env | cut -d '=' -f2 | tr -d ' ')
SERVER_IP=$(hostname -I | awk '{print $1}')

print_status "Summary:"
print_status "- Superuser created with updated user model (username: janak, password: admin123)"
print_status "- Common fixtures loaded (countries, late fee configs)"
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
print_status "- Admin panel fixtures loaded (if available)"
echo ""
print_status "🌐 Your PowerBank API is ready!"
print_status "API Base URL: http://$SERVER_IP:${API_PORT:-8010}"
print_status "API Documentation: http://$SERVER_IP:${API_PORT:-8010}/docs/"
print_status "Admin Panel: http://$SERVER_IP:${API_PORT:-8010}/admin/"
print_status "Health Check: http://$SERVER_IP:${API_PORT:-8010}/api/app/health/"
echo ""
print_status "🔐 Authentication System:"
print_status "- OTP-based registration and login implemented"
print_status "- Admin credentials: username=janak, password=admin123"
print_status "- For API testing, use OTP flow as documented in api/users/AUTH_FLOW.md"
print_status "- Admin JWT token generated above for immediate Swagger UI testing"
print_status "- Regular users must complete OTP verification for registration/login"
echo ""
print_status "🔧 Useful commands:"
print_status "Django shell: docker-compose exec $API_CONTAINER python manage.py shell"
print_status "View logs: docker-compose logs -f $API_CONTAINER"
print_status "Restart API: docker-compose restart $API_CONTAINER"
print_status "Generate admin token: docker-compose exec $API_CONTAINER python manage.py shell -c \"from django.contrib.auth import get_user_model; from rest_framework_simplejwt.tokens import RefreshToken; User = get_user_model(); admin = User.objects.get(username='janak'); print('Admin JWT:', str(RefreshToken.for_user(admin).access_token))\""
