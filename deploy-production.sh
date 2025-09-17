#!/bin/bash

# PowerBank Django Deployment Script
# Deploy to same VPS as existing Java/IoT application

set -e  # Exit on any error

echo "🚀 Starting PowerBank Django Deployment..."
echo "========================================="

# Configuration
PROJECT_DIR="/opt/powerbank"
REPO_URL="https://github.com/itzmejanak/ChargeGhar.git"
BRANCH="main"
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if we're running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root"
   exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please run the server setup script first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not available"
    exit 1
fi

print_status "Docker and Docker Compose are available ✓"

# Create project directory if it doesn't exist
if [[ ! -d "$PROJECT_DIR" ]]; then
    print_status "Creating project directory: $PROJECT_DIR"
    mkdir -p "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"

# Clone or update repository
if [[ -d ".git" ]]; then
    print_status "Updating existing repository..."
    git fetch origin
    git checkout "$BRANCH"
    git pull origin "$BRANCH"
else
    print_status "Cloning repository..."
    git clone "$REPO_URL" .
    git checkout "$BRANCH"
fi

# Check if .env file exists
if [[ ! -f ".env" ]]; then
    print_error ".env file not found! Please ensure the repository contains the .env file."
    exit 1
fi

print_status "Repository is ready ✓"

# Update environment for production
print_status "Updating environment configuration..."
sed -i 's/ENVIRONMENT=local/ENVIRONMENT=production/' .env
sed -i 's/DJANGO_DEBUG=false/DJANGO_DEBUG=false/' .env
sed -i 's/CELERY_TASK_ALWAYS_EAGER=true/CELERY_TASK_ALWAYS_EAGER=false/' .env
sed -i 's/CELERY_TASK_EAGER_PROPAGATES=true/CELERY_TASK_EAGER_PROPAGATES=false/' .env

# Create logs directory
mkdir -p logs

# Stop existing containers if running
print_status "Stopping existing containers..."
docker-compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans || true

# Clean up unused Docker resources
print_status "Cleaning up Docker resources..."
docker system prune -f

# Build and start services
print_status "Building and starting services..."
docker-compose -f "$DOCKER_COMPOSE_FILE" up -d --build

# Wait for services to be ready
print_status "Waiting for services to be ready..."
sleep 45

# Check if services are running
print_status "Checking service status..."
docker-compose -f "$DOCKER_COMPOSE_FILE" ps

# Wait a bit more for API to be fully ready
print_status "Waiting for API to be fully ready..."
sleep 15

# Test health endpoint with retries
print_status "Testing health endpoint..."
API_PORT=$(grep "API_PORT" .env | cut -d '=' -f2 | tr -d ' ')
HEALTH_URL="http://localhost:${API_PORT:-8010}/api/app/health/"

for i in {1..10}; do
    if curl -f "$HEALTH_URL" &> /dev/null; then
        print_status "Health check passed ✓"
        break
    else
        if [ $i -eq 10 ]; then
            print_warning "Health check failed after 10 attempts - checking logs..."
            docker-compose -f "$DOCKER_COMPOSE_FILE" logs --tail=20 powerbank_api
        else
            print_status "Health check attempt $i/10 failed, retrying in 5 seconds..."
            sleep 5
        fi
    fi
done

# Get service URLs
SERVER_IP=$(hostname -I | awk '{print $1}')

print_status ""
print_status "🎉 Deployment completed successfully!"
print_status "========================================="
print_status "PowerBank Django API: http://$SERVER_IP:${API_PORT:-8010}"
print_status "Health Check: $HEALTH_URL"
print_status "API Documentation: http://$SERVER_IP:${API_PORT:-8010}/docs/"
print_status ""
print_status "Useful commands:"
print_status "View logs: docker-compose -f $DOCKER_COMPOSE_FILE logs -f"
print_status "View API logs: docker-compose -f $DOCKER_COMPOSE_FILE logs -f powerbank_api"
print_status "Restart services: docker-compose -f $DOCKER_COMPOSE_FILE restart"
print_status "Stop services: docker-compose -f $DOCKER_COMPOSE_FILE down"
print_status ""
print_status "Load fixtures: ./load-fixtures.sh"
print_status ""
print_status "Note: This deployment runs alongside your existing Java/IoT application"
print_status "Java app (port 8080) and Django app (port ${API_PORT:-8010}) are separate"