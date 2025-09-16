#!/bin/bash

# PowerBank Django Production Deployment Script v2.2
# Enhanced with Git clone/update, collectstatic and automated fixture loading

set -e  # Exit on any error

# Script configuration
PROJECT_NAME="PowerBank Django"
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"
REPO_URL="https://github.com/itzmejanak/ChargeGhar.git"
BRANCH="main"
API_PORT=${API_PORT:-8010}
BACKUP_DIR="/opt/powerbank/backups/$(date +%Y%m%d_%H%M%S)"
ROLLBACK_FILE="/tmp/powerbank_rollback_$(date +%Y%m%d_%H%M%S).sh"

echo "🚀 $PROJECT_NAME Production Deployment v2.2"
echo "=============================================="

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

print_info() {
    echo -e "${BLUE}[DEBUG]${NC} $1"
}

# Function to check command success
check_command() {
    if [[ $? -eq 0 ]]; then
        print_status "✅ $1"
    else
        print_error "❌ Failed: $1"
        return 1
    fi
}

# Function to create rollback script
create_rollback_script() {
    cat > "$ROLLBACK_FILE" << ROLLBACK_EOF
#!/bin/bash
echo "🔄 Rolling back PowerBank deployment..."

# Stop new containers
docker-compose -f $DOCKER_COMPOSE_FILE down || true

# Restore from backup if it exists
if [[ -f "$BACKUP_DIR/docker-compose.yml" ]]; then
    cp "$BACKUP_DIR/docker-compose.yml" .
    docker-compose up -d
    echo "✅ Rollback completed from backup: $BACKUP_DIR"
else
    echo "❌ No backup found for rollback"
fi
ROLLBACK_EOF
    chmod +x "$ROLLBACK_FILE"
    print_status "Rollback script created: $ROLLBACK_FILE"
}

# Function to handle Git clone/update
handle_git_operations() {
    print_info "Handling Git repository operations..."

    if [[ -d ".git" ]]; then
        print_info "Git repository exists. Updating from remote..."
        git fetch origin
        git checkout "$BRANCH"
        git pull origin "$BRANCH"
        print_status "✅ Repository updated successfully"
    else
        print_info "Git repository not found. Cloning from: $REPO_URL"
        local temp_dir="/tmp/powerbank_git_temp"
        rm -rf "$temp_dir" 2>/dev/null || true
        mkdir -p "$temp_dir"

        if git clone "$REPO_URL" "$temp_dir"; then
            cd "$temp_dir"
            git checkout "$BRANCH"
            print_status "✅ Repository cloned successfully"

            # Copy files to working directory
            print_info "Copying repository files..."
            cp -r . /opt/powerbank/
            cd /opt/powerbank

            # Set proper ownership
            chown -R root:root /opt/powerbank 2>/dev/null || true

            # Cleanup temp directory
            rm -rf "$temp_dir"
            print_status "✅ Repository files copied and cleaned up"
        else
            print_error "❌ Failed to clone repository"
            return 1
        fi
    fi

    # Verify repository integrity
    if [[ -f "manage.py" && -f "docker-compose.prod.yml" ]]; then
        print_status "✅ Repository integrity verified"
    else
        print_error "❌ Repository appears incomplete (missing key files)"
        return 1
    fi
}

# Function to run collectstatic before deployment
run_collectstatic() {
    print_info "Running collectstatic before deployment..."

    # Check if collectstatic service exists in docker-compose
    if docker-compose -f "$DOCKER_COMPOSE_FILE" config --services | grep -q "^collectstatic$"; then
        print_info "Running collectstatic in container..."
        if docker-compose -f "$DOCKER_COMPOSE_FILE" run --rm collectstatic --noinput; then
            check_command "Collectstatic completed successfully"
        else
            print_warning "Collectstatic failed, continuing deployment..."
        fi
    else
        print_warning "Collectstatic service not found in docker-compose.prod.yml"
        print_info "Skipping collectstatic step"
    fi
}

# Function to load fixtures after deployment
load_fixtures() {
    print_info "Loading fixtures in dependency order..."

    local fixture_count=0
    local success_count=0

    # Define fixtures in dependency order
    local fixtures=(
        "api/common/fixtures/countries.json"
        "api/common/fixtures/late.json"
        "api/users/fixtures/users.json"
        "api/stations/fixtures/stations.json"
        "api/stations/fixtures/slots_powerbanks.json"
        "api/stations/fixtures/station_additional.json"
        "api/points/fixtures/points.json"
        "api/promotions/fixtures/promotions.json"
        "api/content/fixtures/content.json"
        "api/notifications/fixtures/notifications.json"
        "api/payments/fixtures/payments.json"
        "api/social/fixtures/social.json"
    )

    ((fixture_count = ${#fixtures[@]}))

    for fixture in "${fixtures[@]}"; do
        if [[ -f "$fixture" ]]; then
            print_info "Loading fixture: $fixture"
            if docker-compose -f "$DOCKER_COMPOSE_FILE" run --rm migrations python manage.py loaddata "$fixture" 2>/dev/null; then
                ((success_count++))
                print_status "✅ Loaded: $fixture"
            else
                print_warning "⚠️  Failed to load: $fixture (might not exist or have dependencies)"
            fi
        else
            print_info "Skipping missing fixture: $fixture"
        fi
    done

    print_status "Fixture loading complete: $success_count/$fixture_count fixtures loaded successfully"
}

# Function to resolve port conflicts
resolve_port_conflicts() {
    print_info "Checking for port conflicts on port $API_PORT..."

    # Check if port is in use
    if lsof -Pi :$API_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_warning "Port $API_PORT is already in use!"

        # Find the container using the port
        CONFLICT_CONTAINER=$(docker ps --filter "publish=$API_PORT" --format "{{.Names}}" 2>/dev/null || true)

        if [[ -n "$CONFLICT_CONTAINER" ]]; then
            print_info "Found conflicting container: $CONFLICT_CONTAINER"

            # Create backup of conflicting container info
            mkdir -p "$BACKUP_DIR"
            docker inspect "$CONFLICT_CONTAINER" > "$BACKUP_DIR/conflicting_container.json" 2>/dev/null || true

            # Stop and remove conflicting container
            print_info "Stopping conflicting container..."
            docker stop "$CONFLICT_CONTAINER" 2>/dev/null || true
            docker rm "$CONFLICT_CONTAINER" 2>/dev/null || true

            print_status "Resolved port conflict by removing: $CONFLICT_CONTAINER"
        else
            print_warning "Port $API_PORT in use by non-Docker process"
            print_info "Attempting to kill process using port $API_PORT..."

            # Try to kill the process
            PORT_PID=$(lsof -t -i:$API_PORT 2>/dev/null || true)
            if [[ -n "$PORT_PID" ]]; then
                kill -9 "$PORT_PID" 2>/dev/null || true
                sleep 2
                print_status "Killed process $PORT_PID using port $API_PORT"
            fi
        fi
    else
        print_status "Port $API_PORT is available"
    fi
}

# Function to cleanup old resources
cleanup_old_resources() {
    print_info "Cleaning up old containers and resources..."

    # Stop and remove old containers
    docker-compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans 2>/dev/null || true

    # Remove old networks
    OLD_NETWORKS=$(docker network ls --filter "name=powerbank" --format "{{.Name}}" 2>/dev/null | grep -v "powerbank_production" || true)
    for network in $OLD_NETWORKS; do
        if [[ "$network" != "powerbank_production_powerbank_main" ]]; then
            docker network rm "$network" 2>/dev/null || true
            print_info "Removed old network: $network"
        fi
    done

    # Clean up dangling resources
    docker system prune -f >/dev/null 2>&1 || true
    docker volume prune -f >/dev/null 2>&1 || true

    print_status "Cleanup completed"
}

# Function to validate health checks
validate_health_checks() {
    local max_attempts=30
    local attempt=1

    print_info "Validating application health checks..."

    while [[ $attempt -le $max_attempts ]]; do
        if curl -f -s "http://localhost:$API_PORT/api/app/health/" >/dev/null 2>&1; then
            print_status "✅ Health check passed on attempt $attempt"
            return 0
        fi

        print_info "Health check attempt $attempt/$max_attempts failed, waiting..."
        sleep 5
        ((attempt++))
    done

    print_error "❌ Health check failed after $max_attempts attempts"
    return 1
}

# Function to show deployment summary
show_deployment_summary() {
    echo ""
    print_status "🎉 Deployment Summary"
    print_status "====================="

    # Show container status
    echo "Container Status:"
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

    echo ""
    print_status "🌐 Application URLs:"
    echo "  Django API: http://$SERVER_IP:$API_PORT"
    echo "  Health Check: http://$SERVER_IP:$API_PORT/api/app/health/"
    echo "  API Docs: http://$SERVER_IP:$API_PORT/api/schema/swagger-ui/"

    echo ""
    print_status "🛠️  Management Commands:"
    echo "  View logs: docker-compose -f $DOCKER_COMPOSE_FILE logs -f"
    echo "  Restart: docker-compose -f $DOCKER_COMPOSE_FILE restart"
    echo "  Stop: docker-compose -f $DOCKER_COMPOSE_FILE down"
    echo "  Rollback: $ROLLBACK_FILE"

    echo ""
    print_status "✅ Deployment completed successfully!"
}

# Main deployment function
main() {
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
       print_error "This script must be run as root"
       exit 1
    fi

    # Get server IP
    SERVER_IP=$(hostname -I | awk '{print $1}')

    # Validate environment
    if [[ ! -f ".env" ]]; then
        print_error ".env file not found! Please ensure the .env file exists."
        exit 1
    fi

    # Validate Docker and Docker Compose
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not available"
        exit 1
    fi

    print_status "✅ Pre-deployment validation passed"

    # Create rollback script
    create_rollback_script

    # Handle Git operations (clone or update)
    handle_git_operations

    # Run collectstatic before starting containers
    run_collectstatic

    # Resolve port conflicts
    resolve_port_conflicts

    # Cleanup old resources
    cleanup_old_resources

    # Create backup directory
    mkdir -p "$BACKUP_DIR" 2>/dev/null || true
    cp "$DOCKER_COMPOSE_FILE" "$BACKUP_DIR/" 2>/dev/null || true
    cp ".env" "$BACKUP_DIR/" 2>/dev/null || true

    # Build and start services
    print_status "Building and starting services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d --build
    check_command "Services started successfully"

    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 20

    # Load fixtures after services are ready
    load_fixtures

    # Validate deployment
    if validate_health_checks; then
        show_deployment_summary
    else
        print_error "Deployment validation failed!"
        print_warning "You can try to fix issues and re-run, or use rollback: $ROLLBACK_FILE"
        exit 1
    fi
}

# Trap for cleanup on script exit
trap 'print_warning "Script interrupted. Rollback available at: $ROLLBACK_FILE"' INT TERM

# Run main function
main "$@"