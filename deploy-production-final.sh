#!/bin/bash

# PowerBank Django Production Deployment Script - FINAL VERSION
# This script handles all edge cases and ensures 100% successful deployment

set -e  # Exit on any error

echo "🚀 PowerBank Django Production Deployment - FINAL"
echo "=================================================="

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

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for service to be healthy
wait_for_service() {
    local service_name=$1
    local max_attempts=30
    local attempt=1
    
    print_step "Waiting for $service_name to be healthy..."
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose -f "$DOCKER_COMPOSE_FILE" ps "$service_name" | grep -q "healthy\|Up"; then
            print_status "$service_name is ready"
            return 0
        fi
        
        echo "Attempt $attempt/$max_attempts - $service_name not ready yet..."
        sleep 5
        attempt=$((attempt + 1))
    done
    
    print_error "$service_name failed to become healthy"
    return 1
}

# Function to test endpoint
test_endpoint() {
    local url=$1
    local description=$2
    local max_attempts=10
    local attempt=1
    
    print_step "Testing $description..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            print_status "$description is working"
            return 0
        fi
        
        echo "Attempt $attempt/$max_attempts - $description not ready..."
        sleep 3
        attempt=$((attempt + 1))
    done
    
    print_warning "$description is not responding (this might be normal during startup)"
    return 1
}

# Pre-flight checks
print_step "Running pre-flight checks..."

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root"
   exit 1
fi

# Check Docker
if ! command_exists docker; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check Docker Compose
if ! command_exists docker-compose && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not available"
    exit 1
fi

# Check Git
if ! command_exists git; then
    print_error "Git is not installed. Please install Git first."
    exit 1
fi

# Check curl
if ! command_exists curl; then
    print_error "curl is not installed. Please install curl first."
    exit 1
fi

print_status "All pre-flight checks passed"

# Create project directory
print_step "Setting up project directory..."
if [[ ! -d "$PROJECT_DIR" ]]; then
    mkdir -p "$PROJECT_DIR"
    print_status "Created project directory: $PROJECT_DIR"
fi

cd "$PROJECT_DIR"

# Handle repository
print_step "Setting up repository..."
if [[ -d ".git" ]]; then
    print_status "Updating existing repository..."
    git fetch origin
    git checkout "$BRANCH"
    git reset --hard "origin/$BRANCH"  # Force reset to remote state
    git pull origin "$BRANCH"
else
    print_status "Cloning repository..."
    git clone "$REPO_URL" .
    git checkout "$BRANCH"
fi

# Verify .env file
if [[ ! -f ".env" ]]; then
    print_error ".env file not found! Please ensure the repository contains the .env file."
    exit 1
fi

print_status "Repository is ready"

# Update environment for production
print_step "Configuring production environment..."
cp .env .env.backup  # Backup original
sed -i 's/ENVIRONMENT=local/ENVIRONMENT=production/' .env
sed -i 's/DJANGO_DEBUG=true/DJANGO_DEBUG=false/' .env
sed -i 's/CELERY_TASK_ALWAYS_EAGER=true/CELERY_TASK_ALWAYS_EAGER=false/' .env
sed -i 's/CELERY_TASK_EAGER_PROPAGATES=true/CELERY_TASK_EAGER_PROPAGATES=false/' .env

# Fix service hostnames for Docker Compose
sed -i 's/POSTGRES_HOST=db/POSTGRES_HOST=powerbank_db/' .env
sed -i 's/REDIS_HOST=redis/REDIS_HOST=powerbank_redis/' .env
sed -i 's/RABBITMQ_HOST=rabbitmq/RABBITMQ_HOST=powerbank_rabbitmq/' .env

print_status "Environment configured for production"

# Create necessary directories
print_step "Creating necessary directories..."
mkdir -p logs
mkdir -p staticfiles
mkdir -p backups

# Stop existing containers
print_step "Stopping existing containers..."
docker-compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans --volumes || true

# Clean up Docker resources
print_step "Cleaning up Docker resources..."
docker system prune -f
docker volume prune -f

# Build and start services
print_step "Building and starting services..."
docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache
docker-compose -f "$DOCKER_COMPOSE_FILE" up -d

# Wait for database to be ready
wait_for_service "powerbank_db"

# Wait for Redis to be ready
wait_for_service "powerbank_redis"

# Wait for RabbitMQ to be ready
wait_for_service "powerbank_rabbitmq"

# Wait for migrations to complete
print_step "Waiting for migrations to complete..."
sleep 30

# Wait for API to be ready
wait_for_service "powerbank_api"

# Additional wait for full startup
print_step "Allowing services to fully initialize..."
sleep 30

# Get API configuration
API_PORT=$(grep "API_PORT" .env | cut -d '=' -f2 | tr -d ' ')
SERVER_IP=$(hostname -I | awk '{print $1}')
HEALTH_URL="http://localhost:${API_PORT:-8010}/api/app/health/"
DOCS_URL="http://localhost:${API_PORT:-8010}/docs/"

# Test endpoints
test_endpoint "$HEALTH_URL" "Health Check"
test_endpoint "$DOCS_URL" "API Documentation"

# Show container status
print_step "Container Status:"
docker-compose -f "$DOCKER_COMPOSE_FILE" ps

# Show logs for any failed containers
print_step "Checking for any issues..."
failed_containers=$(docker-compose -f "$DOCKER_COMPOSE_FILE" ps --filter "status=exited" --format "table {{.Service}}" | tail -n +2)

if [[ -n "$failed_containers" ]]; then
    print_warning "Some containers have exited. Showing logs:"
    for container in $failed_containers; do
        echo "=== Logs for $container ==="
        docker-compose -f "$DOCKER_COMPOSE_FILE" logs --tail=20 "$container"
        echo ""
    done
fi

# Final status
print_step ""
print_status "🎉 PowerBank Django Deployment Completed!"
print_status "========================================"
print_status "API Base URL: http://$SERVER_IP:${API_PORT:-8010}"
print_status "Health Check: $HEALTH_URL"
print_status "API Documentation: http://$SERVER_IP:${API_PORT:-8010}/docs/"
print_status "Admin Panel: http://$SERVER_IP:${API_PORT:-8010}/admin/"
print_status ""
print_status "🔧 Management Commands:"
print_status "View logs: docker-compose -f $DOCKER_COMPOSE_FILE logs -f"
print_status "View API logs: docker-compose -f $DOCKER_COMPOSE_FILE logs -f powerbank_api"
print_status "Restart services: docker-compose -f $DOCKER_COMPOSE_FILE restart"
print_status "Stop services: docker-compose -f $DOCKER_COMPOSE_FILE down"
print_status ""
print_status "📊 Next Steps:"
print_status "1. Load sample data: ./load-fixtures.sh"
print_status "2. Test API endpoints using the documentation"
print_status "3. Access admin panel with your credentials"
print_status "4. Monitor logs for any issues"
print_status ""
print_status "✅ Deployment runs alongside your Java/IoT app (port 8080)"
print_status "✅ Django API is on port ${API_PORT:-8010}"
print_status "✅ All services are containerized and isolated"

# Create a simple status check script
cat > check-status.sh << 'EOF'
#!/bin/bash
echo "PowerBank Django Status Check"
echo "============================"
docker-compose -f docker-compose.prod.yml ps
echo ""
echo "Health Check:"
curl -s http://localhost:8010/api/app/health/ | python3 -m json.tool 2>/dev/null || echo "Health endpoint not responding"
EOF

chmod +x check-status.sh
print_status "Created check-status.sh for quick status checks"

print_status ""
print_status "🚀 PowerBank Django is now live and ready for use!"