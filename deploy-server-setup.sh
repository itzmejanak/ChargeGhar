#!/bin/bash

# PowerBank Django Server Setup Script v2.0
# Enhanced with comprehensive validation, error handling, and rollback capabilities

set -e  # Exit on any error

echo "🔧 PowerBank Django Server Setup v2.0"
echo "====================================="

# Script configuration
REQUIRED_DOCKER_VERSION="20.10.0"
REQUIRED_COMPOSE_VERSION="1.29.0"
BACKUP_DIR="/opt/powerbank/setup_backup_$(date +%Y%m%d_%H%M%S)"
ROLLBACK_FILE="/tmp/server_setup_rollback_$(date +%Y%m%d_%H%M%S).sh"

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

# Function to compare versions
version_compare() {
    if [[ $1 == $2 ]]; then
        return 0
    fi
    local IFS=.
    local i ver1=($1) ver2=($2)
    for ((i=${#ver1[@]}; i<${#ver2[@]}; i++)); do
        ver1[i]=0
    done
    for ((i=0; i<${#ver1[@]}; i++)); do
        if [[ -z ${ver2[i]} ]]; then
            ver2[i]=0
        fi
        if ((10#${ver1[i]} > 10#${ver2[i]})); then
            return 1
        fi
        if ((10#${ver1[i]} < 10#${ver2[i]})); then
            return 2
        fi
    done
    return 0
}

# Function to create rollback script
create_rollback_script() {
    cat > "$ROLLBACK_FILE" << EOF
#!/bin/bash
echo "🔄 Rolling back server setup..."

# Remove installed packages if they were installed by this script
if [[ -f "$BACKUP_DIR/installed_packages.txt" ]]; then
    echo "Removing installed packages..."
    xargs apt-get remove -y < "$BACKUP_DIR/installed_packages.txt" || true
fi

# Restore original configurations
if [[ -f "$BACKUP_DIR/original_docker.service" ]]; then
    cp "$BACKUP_DIR/original_docker.service" /lib/systemd/system/docker.service
    systemctl daemon-reload
fi

echo "✅ Rollback completed. Original state restored from: $BACKUP_DIR"
EOF
    chmod +x "$ROLLBACK_FILE"
    print_status "Rollback script created: $ROLLBACK_FILE"
}

# Function to backup current state
backup_current_state() {
    print_info "Creating backup of current state..."

    mkdir -p "$BACKUP_DIR"

    # Backup package list
    dpkg --get-selections > "$BACKUP_DIR/installed_packages.txt" 2>/dev/null || true

    # Backup Docker configuration if it exists
    if [[ -f "/lib/systemd/system/docker.service" ]]; then
        cp "/lib/systemd/system/docker.service" "$BACKUP_DIR/original_docker.service"
    fi

    # Backup environment
    env > "$BACKUP_DIR/environment.txt"
    uname -a > "$BACKUP_DIR/system_info.txt"

    print_status "Backup created at: $BACKUP_DIR"
}

# Function to check system requirements
check_system_requirements() {
    print_info "Checking system requirements..."

    # Check Ubuntu version
    if [[ ! -f "/etc/os-release" ]]; then
        print_error "This script is designed for Ubuntu/Debian systems"
        exit 1
    fi

    source /etc/os-release
    if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
        print_warning "This script is optimized for Ubuntu/Debian. Detected: $ID $VERSION"
    else
        print_status "✅ Detected $PRETTY_NAME"
    fi

    # Check available memory
    local total_mem=$(free -m | grep '^Mem:' | awk '{print $2}')
    if [[ $total_mem -lt 1024 ]]; then
        print_warning "System has ${total_mem}MB RAM. Recommended: 2048MB+"
        print_warning "Deployment may be slow or unstable"
    else
        print_status "✅ Sufficient memory: ${total_mem}MB"
    fi

    # Check available disk space
    local available_space=$(df / | tail -1 | awk '{print $4}')
    if [[ $available_space -lt 5242880 ]]; then  # 5GB in KB
        print_warning "Low disk space: $(($available_space/1024/1024))GB available"
        print_warning "Recommended: 10GB+ free space"
    else
        print_status "✅ Sufficient disk space available"
    fi
}

# Function to install Docker
install_docker() {
    print_info "Installing Docker..."

    # Remove old versions
    apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true

    # Update package index
    apt-get update
    check_command "Package index updated"

    # Install required packages
    apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    check_command "Required packages installed"

    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    check_command "Docker GPG key added"

    # Set up stable repository
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    check_command "Docker repository added"

    # Install Docker Engine
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    check_command "Docker Engine installed"

    # Start and enable Docker
    systemctl start docker
    systemctl enable docker
    check_command "Docker service started and enabled"
}

# Function to install Docker Compose
install_docker_compose() {
    print_info "Installing Docker Compose..."

    # Remove old versions
    rm -f /usr/local/bin/docker-compose 2>/dev/null || true
    rm -f /usr/bin/docker-compose 2>/dev/null || true

    # Install Docker Compose v2 (plugin)
    if ! docker compose version &>/dev/null; then
        print_info "Installing Docker Compose v2 plugin..."
        apt-get install -y docker-compose-plugin
    fi

    # Fallback to Docker Compose v1 if plugin fails
    if ! docker compose version &>/dev/null; then
        print_info "Installing Docker Compose v1 as fallback..."
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
            -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
        ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose
    fi

    check_command "Docker Compose installed"
}

# Function to validate installations
validate_installations() {
    print_info "Validating installations..."

    # Check Docker version
    local docker_version=$(docker --version | grep -oP 'Docker version \K[^,]+')
    if [[ -z "$docker_version" ]]; then
        print_error "Docker version check failed"
        return 1
    fi

    version_compare "$docker_version" "$REQUIRED_DOCKER_VERSION"
    case $? in
        0) print_status "✅ Docker version: $docker_version (exact match)" ;;
        1) print_status "✅ Docker version: $docker_version (newer than required)" ;;
        2) print_warning "⚠️  Docker version: $docker_version (older than recommended $REQUIRED_DOCKER_VERSION)" ;;
    esac

    # Check Docker Compose version
    local compose_version=""
    if docker compose version &>/dev/null; then
        compose_version=$(docker compose version | grep -oP 'v\K[^ ]+')
        print_status "✅ Docker Compose v2: $compose_version"
    elif docker-compose --version &>/dev/null; then
        compose_version=$(docker-compose --version | grep -oP 'version \K[^,]+')
        print_status "✅ Docker Compose v1: $compose_version"
    else
        print_error "Docker Compose not found"
        return 1
    fi

    # Test Docker functionality
    if docker run --rm hello-world &>/dev/null; then
        print_status "✅ Docker functionality test passed"
    else
        print_error "Docker functionality test failed"
        return 1
    fi

    return 0
}

# Function to setup PowerBank user and permissions
setup_powerbank_user() {
    print_info "Setting up PowerBank user and permissions..."

    # Create powerbank user if it doesn't exist
    if ! id -u powerbank &>/dev/null; then
        useradd -m -s /bin/bash powerbank
        print_status "✅ User 'powerbank' created"
    else
        print_status "✅ User 'powerbank' already exists"
    fi

    # Add powerbank user to docker group
    if ! groups powerbank | grep -q docker; then
        usermod -aG docker powerbank
        print_status "✅ User 'powerbank' added to docker group"
    fi

    # Create project directory
    local project_dir="/opt/powerbank"
    if [[ ! -d "$project_dir" ]]; then
        mkdir -p "$project_dir"
        chown powerbank:powerbank "$project_dir"
        print_status "✅ Project directory created: $project_dir"
    else
        print_status "✅ Project directory exists: $project_dir"
    fi
}

# Function to show setup summary
show_setup_summary() {
    echo ""
    print_status "🎉 Server Setup Summary"
    print_status "======================="

    echo "Docker Version: $(docker --version)"
    echo "Docker Compose: $(docker compose version 2>/dev/null || docker-compose --version)"

    echo ""
    print_status "📁 Project Directory: /opt/powerbank"
    print_status "👤 PowerBank User: powerbank (in docker group)"
    print_status "🔄 Rollback Script: $ROLLBACK_FILE"
    print_status "💾 Backup Location: $BACKUP_DIR"

    echo ""
    print_status "🚀 Next Steps:"
    echo "1. Switch to powerbank user: su - powerbank"
    echo "2. Navigate to project: cd /opt/powerbank"
    echo "3. Run deployment: ./deploy-production.sh"

    echo ""
    print_status "✅ Server setup completed successfully!"
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

# Main setup function
main() {
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
       print_error "This script must be run as root"
       exit 1
    fi

    print_status "Starting PowerBank server setup..."

    # Create rollback script
    create_rollback_script

    # Backup current state
    backup_current_state

    # Check system requirements
    check_system_requirements

    # Install Docker if not present
    if ! command -v docker &> /dev/null; then
        print_info "Docker not found. Installing..."
        install_docker
    else
        print_status "✅ Docker is already installed"
    fi

    # Install Docker Compose if not present
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_info "Docker Compose not found. Installing..."
        install_docker_compose
    else
        print_status "✅ Docker Compose is available"
    fi

    # Validate installations
    if ! validate_installations; then
        print_error "Installation validation failed!"
        print_warning "You can try to fix issues manually or use rollback: $ROLLBACK_FILE"
        exit 1
    fi

    # Setup PowerBank user and permissions
    setup_powerbank_user

    # Show setup summary
    show_setup_summary
}

# Trap for cleanup on script exit
trap 'print_warning "Setup interrupted. Rollback available at: $ROLLBACK_FILE"' INT TERM

# Run main function
main "$@"