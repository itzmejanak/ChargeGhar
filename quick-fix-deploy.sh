#!/bin/bash

# Quick fix and deploy script
set -e

echo "🔧 Quick Fix and Deploy"
echo "======================"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_step() {
    echo -e "${YELLOW}[STEP]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Stop everything
print_step "Stopping all containers..."
docker-compose -f docker-compose.prod.yml down --remove-orphans --volumes || true

# Clean up
print_step "Cleaning up Docker resources..."
docker system prune -f

# Build only (to test if build works)
print_step "Testing build..."
if docker-compose -f docker-compose.prod.yml build --no-cache; then
    print_status "Build successful!"
else
    print_error "Build failed!"
    exit 1
fi

# Start services
print_step "Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait and check
print_step "Waiting 30 seconds for services to start..."
sleep 30

# Check container status
print_step "Container status:"
docker-compose -f docker-compose.prod.yml ps

# Check migration logs
print_step "Migration logs:"
docker-compose -f docker-compose.prod.yml logs powerbank_migrations

# Check collectstatic logs
print_step "Collectstatic logs:"
docker-compose -f docker-compose.prod.yml logs powerbank_collectstatic

# Test health if API is running
print_step "Testing health endpoint..."
sleep 10
if curl -f -s "http://localhost:8010/api/app/health/" > /dev/null 2>&1; then
    print_status "Health check passed!"
    echo "API Response:"
    curl -s "http://localhost:8010/api/app/health/" | python3 -m json.tool 2>/dev/null || echo "Raw response: $(curl -s http://localhost:8010/api/app/health/)"
else
    print_error "Health check failed, checking API logs..."
    docker-compose -f docker-compose.prod.yml logs --tail=20 powerbank_api
fi

print_status "Quick fix deployment completed!"