#!/bin/bash

# PowerBank Django Production Deployment Script
# Clean deployment focused on containers and fixtures

set -e  # Exit on any error

echo "🚀 PowerBank Django Production Deployment"
echo "=========================================="

# Configuration
PROJECT_DIR="/opt/powerbank"
REPO_URL="https://github.com/itzmejanak/ChargeGhar.git"
BRANCH="main"
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root"
   exit 1
fi

# Create and navigate to project directory
if [[ ! -d "$PROJECT_DIR" ]]; then
    mkdir -p "$PROJECT_DIR"
fi
cd "$PROJECT_DIR"

# Update repository
print_step "Updating repository..."
if [[ -d ".git" ]]; then
    git fetch origin
    git checkout "$BRANCH"
    git reset --hard "origin/$BRANCH"
    git pull origin "$BRANCH"
else
    git clone "$REPO_URL" .
    git checkout "$BRANCH"
fi
print_status "Repository updated"

# Configure environment for production
print_step "Configuring production environment..."
cp .env .env.backup 2>/dev/null || true
sed -i 's/ENVIRONMENT=local/ENVIRONMENT=production/' .env
sed -i 's/DJANGO_DEBUG=true/DJANGO_DEBUG=false/' .env
sed -i 's/CELERY_TASK_ALWAYS_EAGER=true/CELERY_TASK_ALWAYS_EAGER=false/' .env
sed -i 's/CELERY_TASK_EAGER_PROPAGATES=true/CELERY_TASK_EAGER_PROPAGATES=false/' .env
sed -i 's/POSTGRES_HOST=db/POSTGRES_HOST=powerbank_db/' .env
sed -i 's/REDIS_HOST=redis/REDIS_HOST=powerbank_redis/' .env
sed -i 's/RABBITMQ_HOST=rabbitmq/RABBITMQ_HOST=powerbank_rabbitmq/' .env
print_status "Environment configured"

# Create directories
mkdir -p logs staticfiles backups

# Stop existing containers and clean up
print_step "Stopping containers and cleaning up..."
docker-compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans --volumes || true

# Kill any containers using port 8010
print_step "Checking for port conflicts..."
API_PORT=$(grep "API_PORT" .env | cut -d '=' -f2 | tr -d ' ')
PORT_TO_CHECK=${API_PORT:-8010}

# Find and stop containers using the port
CONFLICTING_CONTAINERS=$(docker ps --filter "publish=$PORT_TO_CHECK" --format "{{.Names}}" 2>/dev/null || true)
if [[ -n "$CONFLICTING_CONTAINERS" ]]; then
    print_step "Found containers using port $PORT_TO_CHECK, stopping them..."
    echo "$CONFLICTING_CONTAINERS" | while read container; do
        echo "Stopping container: $container"
        docker stop "$container" || true
        docker rm "$container" || true
    done
fi

# Also check for any remaining processes on the port
PROCESS_ON_PORT=$(netstat -tlnp 2>/dev/null | grep ":$PORT_TO_CHECK " | awk '{print $7}' | cut -d'/' -f1 || true)
if [[ -n "$PROCESS_ON_PORT" && "$PROCESS_ON_PORT" != "-" ]]; then
    print_step "Killing process $PROCESS_ON_PORT using port $PORT_TO_CHECK..."
    kill -9 "$PROCESS_ON_PORT" 2>/dev/null || true
fi

docker system prune -f
print_status "Cleanup completed"

# Build and start services
print_step "Building and starting services..."
docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache
docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
print_status "Services started"

# Wait for services to be ready
print_step "Waiting for services to initialize..."
sleep 60

# Show container status
print_step "Container Status:"
docker-compose -f "$DOCKER_COMPOSE_FILE" ps

# Auto-load fixtures
print_step "Loading fixtures..."
if [[ -f "load-fixtures.sh" ]]; then
    chmod +x load-fixtures.sh
    ./load-fixtures.sh
    print_status "Fixtures loaded"
else
    print_error "load-fixtures.sh not found, skipping fixture loading"
fi

# Final status
API_PORT=$(grep "API_PORT" .env | cut -d '=' -f2 | tr -d ' ')
SERVER_IP=$(hostname -I | awk '{print $1}')

print_step ""
print_status "🎉 PowerBank Django Deployment Completed!"
print_status "========================================"
print_status "API URL: https://main.chargeghar.com"
print_status "API Documentation: https://main.chargeghar.com/docs/"
print_status "Admin Panel: https://main.chargeghar.com/admin/"
print_status ""
print_status "Use 'python3 powerbank-manager.py' for management tasks"
print_status ""