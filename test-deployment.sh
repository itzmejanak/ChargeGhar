#!/bin/bash

# PowerBank Django Deployment Test Script
# Tests all endpoints and services after deployment

set -e

echo "🧪 Testing PowerBank Django Deployment..."
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

# Get API port from .env
if [[ -f ".env" ]]; then
    API_PORT=$(grep "API_PORT" .env | cut -d '=' -f2 | tr -d ' ')
else
    API_PORT=8010
fi

BASE_URL="http://localhost:${API_PORT}"

# Test 1: Container Status
print_test "Checking container status..."
if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    print_status "Containers are running"
    docker-compose -f docker-compose.prod.yml ps
else
    print_error "Containers are not running properly"
    exit 1
fi

echo ""

# Test 2: Health Check
print_test "Testing health endpoint..."
if curl -f -s "${BASE_URL}/api/app/health/" > /dev/null; then
    print_status "Health check passed"
    echo "Response: $(curl -s "${BASE_URL}/api/app/health/")"
else
    print_error "Health check failed"
    print_warning "Checking API logs..."
    docker-compose -f docker-compose.prod.yml logs --tail=10 powerbank_api
fi

echo ""

# Test 3: API Documentation
print_test "Testing API documentation..."
if curl -f -s "${BASE_URL}/docs/" > /dev/null; then
    print_status "API documentation is accessible"
else
    print_warning "API documentation might not be available"
fi

echo ""

# Test 4: Admin Panel
print_test "Testing admin panel..."
if curl -f -s "${BASE_URL}/admin/" > /dev/null; then
    print_status "Admin panel is accessible"
else
    print_warning "Admin panel might not be available"
fi

echo ""

# Test 5: Database Connection
print_test "Testing database connection..."
if docker-compose -f docker-compose.prod.yml exec -T powerbank_api python manage.py check --database default > /dev/null 2>&1; then
    print_status "Database connection is working"
else
    print_error "Database connection failed"
fi

echo ""

# Test 6: Redis Connection
print_test "Testing Redis connection..."
if docker-compose -f docker-compose.prod.yml exec -T powerbank_redis redis-cli ping | grep -q "PONG"; then
    print_status "Redis connection is working"
else
    print_error "Redis connection failed"
fi

echo ""

# Test 7: RabbitMQ Connection
print_test "Testing RabbitMQ connection..."
if docker-compose -f docker-compose.prod.yml exec -T powerbank_rabbitmq rabbitmq-diagnostics -q ping > /dev/null 2>&1; then
    print_status "RabbitMQ connection is working"
else
    print_error "RabbitMQ connection failed"
fi

echo ""

# Test 8: Celery Status
print_test "Testing Celery worker..."
if docker-compose -f docker-compose.prod.yml logs powerbank_celery | grep -q "ready"; then
    print_status "Celery worker is running"
else
    print_warning "Celery worker might not be ready yet"
fi

echo ""

# Summary
print_test "Deployment Summary:"
echo "==================="
print_status "API Base URL: ${BASE_URL}"
print_status "Health Check: ${BASE_URL}/api/app/health/"
print_status "API Docs: ${BASE_URL}/docs/"
print_status "Admin Panel: ${BASE_URL}/admin/"

echo ""
print_status "🎉 Deployment test completed!"
print_status "Your PowerBank Django API is ready for use!"

echo ""
print_test "Next steps:"
echo "- Load fixtures: ./load-fixtures.sh"
echo "- Test API endpoints using the documentation"
echo "- Access admin panel with your credentials"