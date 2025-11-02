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
print_step "Repository Management..."
if [[ -d ".git" ]]; then
    # Show current git status
    echo ""
    echo -e "${YELLOW}Current Git Status:${NC}"
    echo "Branch: $(git branch --show-current)"
    echo "Last commit: $(git log -1 --oneline)"
    echo ""
    
    # Show available branches
    echo -e "${YELLOW}Available branches:${NC}"
    git branch -a | grep -E "(main|master|develop|staging)" | head -5
    echo ""
    
    # Interactive menu for git operations
    echo -e "${BLUE}Git Update Options:${NC}"
    echo "1. 🔄 Pull latest from current branch ($(git branch --show-current))"
    echo "2. 🔀 Switch to main branch and pull"
    echo "3. 🔀 Switch to different branch"
    echo "4. 🗑️  Hard reset to remote (discards local changes)"
    echo "5. 💾 Stash changes and pull"
    echo "6. ⏭️  Skip git update (use current code)"
    echo ""
    
    read -p "Select option (1-6): " git_choice
    
    case $git_choice in
        1)
            print_step "Pulling latest from current branch..."
            git pull origin "$(git branch --show-current)"
            ;;
        2)
            print_step "Switching to main branch and pulling..."
            git stash push -m "Auto-stash before switching to main $(date)" || true
            git checkout "$BRANCH" || git checkout -b "$BRANCH" "origin/$BRANCH"
            git pull origin "$BRANCH"
            ;;
        3)
            echo ""
            echo -e "${YELLOW}Available branches:${NC}"
            git branch -a | sed 's/remotes\/origin\///' | grep -v HEAD | sort | uniq | nl
            echo ""
            read -p "Enter branch name: " custom_branch
            if [[ -n "$custom_branch" ]]; then
                print_step "Switching to branch: $custom_branch"
                git stash push -m "Auto-stash before switching to $custom_branch $(date)" || true
                git checkout "$custom_branch" || git checkout -b "$custom_branch" "origin/$custom_branch"
                git pull origin "$custom_branch" || true
                BRANCH="$custom_branch"  # Update branch variable
            else
                print_error "No branch specified, using current branch"
            fi
            ;;
        4)
            print_step "Hard reset to remote (WARNING: This will discard local changes)..."
            read -p "Are you sure? Type 'YES' to confirm: " confirm
            if [[ "$confirm" == "YES" ]]; then
                git fetch origin
                git reset --hard "origin/$(git branch --show-current)"
                print_status "Hard reset completed"
            else
                print_status "Hard reset cancelled"
            fi
            ;;
        5)
            print_step "Stashing changes and pulling..."
            git stash push -m "Manual stash before deployment $(date)"
            git pull origin "$(git branch --show-current)"
            ;;
        6)
            print_status "Skipping git update, using current code"
            ;;
        *)
            print_error "Invalid choice, defaulting to pull current branch"
            git pull origin "$(git branch --show-current)" || true
            ;;
    esac
    
    print_status "Repository updated"
else
    print_step "Cloning repository for first time..."
    git clone "$REPO_URL" .
    git checkout "$BRANCH"
    print_status "Repository cloned"
fi

# Configure environment for production
print_step "Configuring production environment..."
cp .env .env.backup 2>/dev/null || true
sed -i 's|ENVIRONMENT=local|ENVIRONMENT=production|' .env
sed -i 's|DJANGO_DEBUG=true|DJANGO_DEBUG=false|' .env
sed -i 's|CELERY_TASK_ALWAYS_EAGER=true|CELERY_TASK_ALWAYS_EAGER=false|' .env
sed -i 's|CELERY_TASK_EAGER_PROPAGATES=true|CELERY_TASK_EAGER_PROPAGATES=false|' .env
sed -i 's|CELERY_TASK_IGNORE_RESULT=true|CELERY_TASK_IGNORE_RESULT=false|' .env
# Update service names to match production docker-compose
sed -i 's|POSTGRES_HOST=pgbouncer|POSTGRES_HOST=powerbank_db|' .env
sed -i 's|POSTGRES_HOST=db|POSTGRES_HOST=powerbank_db|' .env
sed -i 's|REDIS_HOST=redis|REDIS_HOST=powerbank_redis|' .env
sed -i 's|RABBITMQ_HOST=rabbitmq|RABBITMQ_HOST=powerbank_rabbitmq|' .env
sed -i 's|BASE_URL=http://localhost:8010|BASE_URL=https://main.chargeghar.com|' .env
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
sleep 30

# Check migration status
print_step "Checking migration status..."
if docker-compose -f "$DOCKER_COMPOSE_FILE" ps powerbank_migrations | grep -q "Exit 0"; then
    print_status "Migrations completed successfully"
elif docker-compose -f "$DOCKER_COMPOSE_FILE" ps powerbank_migrations | grep -q "Exit"; then
    print_error "Migrations failed! Checking logs..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" logs powerbank_migrations
    exit 1
else
    print_step "Migrations still running, waiting..."
    sleep 30
fi

# Ensure static files are collected
print_step "Collecting static files..."
docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T powerbank_api python manage.py collectstatic --noinput || true

# Show container status
print_step "Container Status:"
docker-compose -f "$DOCKER_COMPOSE_FILE" ps

# Check for any failed services (excluding successful one-time services)
print_step "Checking for failed services..."
FAILED_SERVICES=$(docker-compose -f "$DOCKER_COMPOSE_FILE" ps --filter "status=exited" --format "table {{.Service}}\t{{.Status}}" | grep -v "SERVICE" | grep -v "Exit 0" | grep -v "powerbank_migrations" | grep -v "powerbank_collectstatic" || true)
if [[ -n "$FAILED_SERVICES" ]]; then
    print_error "Some services failed:"
    echo "$FAILED_SERVICES"
    print_step "Showing logs for failed services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" logs --tail=50
    exit 1
else
    print_status "All services are running successfully!"
    
    # Check one-time services completed successfully
    MIGRATION_STATUS=$(docker-compose -f "$DOCKER_COMPOSE_FILE" ps powerbank_migrations --format "{{.Status}}" | grep "Exit 0" || echo "")
    COLLECTSTATIC_STATUS=$(docker-compose -f "$DOCKER_COMPOSE_FILE" ps powerbank_collectstatic --format "{{.Status}}" | grep "Exit 0" || echo "")
    
    if [[ -n "$MIGRATION_STATUS" ]]; then
        print_status "✅ Database migrations completed successfully"
    fi
    
    if [[ -n "$COLLECTSTATIC_STATUS" ]]; then
        print_status "✅ Static files collection completed successfully"
    fi
fi

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