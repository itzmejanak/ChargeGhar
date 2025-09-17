#!/bin/bash

# Quick redeploy script with fixes
set -e

echo "🔧 Redeploying PowerBank with fixes..."
echo "====================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_step() {
    echo -e "${YELLOW}[STEP]${NC} $1"
}

# Stop existing containers
print_step "Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down --remove-orphans --volumes

# Clean up
print_step "Cleaning up Docker resources..."
docker system prune -f

# Rebuild with no cache
print_step "Rebuilding containers..."
docker-compose -f docker-compose.prod.yml build --no-cache

# Start services
print_step "Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services
print_step "Waiting for services to be ready..."
sleep 60

# Check status
print_step "Checking container status..."
docker-compose -f docker-compose.prod.yml ps

# Check logs for migrations
print_step "Checking migration logs..."
docker-compose -f docker-compose.prod.yml logs powerbank_migrations

# Check logs for collectstatic
print_step "Checking collectstatic logs..."
docker-compose -f docker-compose.prod.yml logs powerbank_collectstatic

# Test health endpoint
print_step "Testing health endpoint..."
sleep 10
if curl -f -s "http://localhost:8010/api/app/health/" > /dev/null; then
    print_status "Health check passed!"
else
    echo "Health check failed, checking API logs..."
    docker-compose -f docker-compose.prod.yml logs --tail=20 powerbank_api
fi

print_status "Redeploy completed!"