#!/bin/bash

# PowerBank Django Production Deployment Script
# Clean deployment focused on containers and fixtures

set -e

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
NC='\033[0m'

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
[[ ! -d "$PROJECT_DIR" ]] && mkdir -p "$PROJECT_DIR"
cd "$PROJECT_DIR"

# Update repository
print_step "Repository Management..."
if [[ -d ".git" ]]; then
    echo ""
    echo -e "${YELLOW}Current Git Status:${NC}"
    echo "Branch: $(git branch --show-current)"
    echo "Last commit: $(git log -1 --oneline)"
    echo ""
    echo -e "${YELLOW}Available branches:${NC}"
    git branch -a | grep -E "(main|master|develop|staging)" | head -5
    echo ""
    
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
            git pull origin "$(git branch --show-current)"
            ;;
        2)
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
                git stash push -m "Auto-stash before switching to $custom_branch $(date)" || true
                git checkout "$custom_branch" || git checkout -b "$custom_branch" "origin/$custom_branch"
                git pull origin "$custom_branch" || true
                BRANCH="$custom_branch"
            else
                print_error "No branch specified, using current branch"
            fi
            ;;
        4)
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
            git stash push -m "Manual stash before deployment $(date)"
            git pull origin "$(git branch --show-current)"
            ;;
        6)
            print_status "Skipping git update"
            ;;
        *)
            print_error "Invalid choice, defaulting to pull current branch"
            git pull origin "$(git branch --show-current)" || true
            ;;
    esac
    
    print_status "Repository updated"
else
    git clone "$REPO_URL" .
    git checkout "$BRANCH"
    print_status "Repository cloned"
fi

# Configure environment for production
print_step "Configuring production environment..."
cp .env .env.backup 2>/dev/null || true

sed -i 's/ENVIRONMENT=local/ENVIRONMENT=production/' .env
sed -i 's/DJANGO_DEBUG=true/DJANGO_DEBUG=false/' .env
sed -i 's/CELERY_TASK_ALWAYS_EAGER=true/CELERY_TASK_ALWAYS_EAGER=false/' .env
sed -i 's/CELERY_TASK_EAGER_PROPAGATES=true/CELERY_TASK_EAGER_PROPAGATES=false/' .env

sed -i 's|HOST=.*|HOST=main.chargeghar.com|' .env
sed -i 's|ALLOWED_HOSTS=.*|ALLOWED_HOSTS=main.chargeghar.com,127.0.0.1,localhost|' .env
sed -i 's|CORS_ALLOWED_ORIGINS=.*|CORS_ALLOWED_ORIGINS=https://main.chargeghar.com,http://main.chargeghar.com|' .env
sed -i 's|CSRF_TRUSTED_ORIGINS=.*|CSRF_TRUSTED_ORIGINS=https://main.chargeghar.com,http://main.chargeghar.com|' .env

sed -i 's|SOCIAL_AUTH_REDIRECT_URL=.*|SOCIAL_AUTH_REDIRECT_URL=https://main.chargeghar.com/auth/social/callback/|' .env
sed -i 's|SOCIAL_AUTH_LOGIN_REDIRECT_URL=.*|SOCIAL_AUTH_LOGIN_REDIRECT_URL=/api/auth/social/success/|' .env
sed -i 's|SOCIAL_AUTH_LOGIN_ERROR_URL=.*|SOCIAL_AUTH_LOGIN_ERROR_URL=/api/auth/social/error/|' .env

sed -i 's/POSTGRES_HOST=pgbouncer/POSTGRES_HOST=powerbank_db/' .env
sed -i 's/POSTGRES_HOST=db/POSTGRES_HOST=powerbank_db/' .env
sed -i 's/REDIS_HOST=redis/REDIS_HOST=powerbank_redis/' .env
sed -i 's/RABBITMQ_HOST=rabbitmq/RABBITMQ_HOST=powerbank_rabbitmq/' .env

sed -i 's/USE_S3_FOR_MEDIA=false/USE_S3_FOR_MEDIA=true/' .env
sed -i 's/USE_S3_FOR_STATIC=false/USE_S3_FOR_STATIC=true/' .env
sed -i 's/USE_REDIS_FOR_CACHE=false/USE_REDIS_FOR_CACHE=true/' .env
sed -i 's/USE_SENTRY=false/USE_SENTRY=true/' .env

sed -i 's/CORS_ORIGIN_ALLOW_ALL=true/CORS_ORIGIN_ALLOW_ALL=false/' .env
sed -i 's/CORS_ALLOW_CREDENTIALS=false/CORS_ALLOW_CREDENTIALS=true/' .env

print_status "Production environment configured"

mkdir -p logs staticfiles backups

# Stop existing containers and clean up
print_step "Stopping containers..."
docker-compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans --volumes || true

# Kill any containers using port
API_PORT=$(grep "API_PORT" .env | cut -d '=' -f2 | tr -d ' ')
PORT_TO_CHECK=${API_PORT:-8010}

CONFLICTING_CONTAINERS=$(docker ps --filter "publish=$PORT_TO_CHECK" --format "{{.Names}}" 2>/dev/null || true)
if [[ -n "$CONFLICTING_CONTAINERS" ]]; then
    echo "$CONFLICTING_CONTAINERS" | while read container; do
        docker stop "$container" || true
        docker rm "$container" || true
    done
fi

PROCESS_ON_PORT=$(netstat -tlnp 2>/dev/null | grep ":$PORT_TO_CHECK " | awk '{print $7}' | cut -d'/' -f1 || true)
if [[ -n "$PROCESS_ON_PORT" && "$PROCESS_ON_PORT" != "-" ]]; then
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
if docker-compose -f "$DOCKER_COMPOSE_FILE" ps powerbank_migrations | grep -q "Exit 0"; then
    print_status "Migrations completed"
elif docker-compose -f "$DOCKER_COMPOSE_FILE" ps powerbank_migrations | grep -q "Exit"; then
    print_error "Migrations failed! Checking logs..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" logs powerbank_migrations
    exit 1
else
    sleep 30
fi

# Collect static files
docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T powerbank_api python manage.py collectstatic --noinput || true

# Show container status
print_step "Container Status:"
docker-compose -f "$DOCKER_COMPOSE_FILE" ps

# Check for failed services
FAILED_SERVICES=$(docker-compose -f "$DOCKER_COMPOSE_FILE" ps --filter "status=exited" --format "table {{.Service}}\t{{.Status}}" | grep -v "SERVICE" | grep -v "Exit 0" | grep -v "powerbank_migrations" | grep -v "powerbank_collectstatic" || true)
if [[ -n "$FAILED_SERVICES" ]]; then
    print_error "Some services failed:"
    echo "$FAILED_SERVICES"
    docker-compose -f "$DOCKER_COMPOSE_FILE" logs --tail=50
    exit 1
else
    print_status "All services running successfully"
    
    MIGRATION_STATUS=$(docker-compose -f "$DOCKER_COMPOSE_FILE" ps powerbank_migrations --format "{{.Status}}" | grep "Exit 0" || echo "")
    COLLECTSTATIC_STATUS=$(docker-compose -f "$DOCKER_COMPOSE_FILE" ps powerbank_collectstatic --format "{{.Status}}" | grep "Exit 0" || echo "")
    
    [[ -n "$MIGRATION_STATUS" ]] && print_status "✅ Database migrations completed"
    [[ -n "$COLLECTSTATIC_STATUS" ]] && print_status "✅ Static files collected"
fi

# Load fixtures
print_step "Loading fixtures..."
if [[ -f "load-fixtures.sh" ]]; then
    chmod +x load-fixtures.sh
    ./load-fixtures.sh
    print_status "Fixtures loaded"
else
    print_error "load-fixtures.sh not found"
fi

# Final status
echo ""
print_status "🎉 Deployment Completed!"
print_status "API URL: https://main.chargeghar.com"
print_status "API Docs: https://main.chargeghar.com/docs/"
print_status "Admin: https://main.chargeghar.com/admin/"
print_status ""
print_status "Use 'python3 powerbank-manager.py' for management tasks"