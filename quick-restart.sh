#!/bin/bash

# Quick restart to fix static files
echo "🔄 Quick Restart to Fix Static Files"
echo "===================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

# Stop API container
print_step "Stopping API container..."
docker-compose -f docker-compose.prod.yml stop powerbank_api

# Remove collectstatic container (no longer needed)
print_step "Removing collectstatic container..."
docker-compose -f docker-compose.prod.yml rm -f powerbank_collectstatic || true

# Start API container (it will collect static files automatically)
print_step "Starting API container with static files collection..."
docker-compose -f docker-compose.prod.yml up -d powerbank_api

# Wait for startup
print_step "Waiting for API to be ready..."
sleep 30

# Test static files
print_step "Testing static files..."
python3 fix-static-files.py

print_status "Quick restart completed!"
print_status "Check: https://main.chargeghar.com/admin/ (should have proper styling now)"