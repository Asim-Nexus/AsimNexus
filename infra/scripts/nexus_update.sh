#!/bin/bash

# ASIMNEXUS Self-Update Engine
# ==========================
# One-click GitHub Auto-Deploy System
# Pulls latest code, rebuilds Docker, restarts services

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/asimnexus/asimnexus.git"
BRANCH="main"
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
LOG_FILE="./logs/nexus_update_$(date +%Y%m%d_%H%M%S).log"
DOCKER_COMPOSE_FILE="docker-compose.awakening.yml"
SERVICES_TO_RESTART=("backend" "frontend" "gpu-worker" "system-optimizer")

# Create log directory
mkdir -p logs backups

echo -e "${CYAN}🧠 ASIMNEXUS Self-Update Engine${NC}"
echo -e "${CYAN}=====================================${NC}"
echo -e "${BLUE}📅 Update started at: $(date)${NC}"
echo -e "${BLUE}📝 Log file: $LOG_FILE${NC}"
echo ""

# Function to log messages
log_message() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

# Function to check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_message "${RED}❌ This script should not be run as root${NC}"
        exit 1
    fi
}

# Function to check Docker status
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_message "${RED}❌ Docker is not installed or not in PATH${NC}"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_message "${RED}❌ Docker daemon is not running${NC}"
        exit 1
    fi
    
    log_message "${GREEN}✅ Docker is running${NC}"
}

# Function to check Docker Compose
check_docker_compose() {
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_message "${RED}❌ Docker Compose is not installed${NC}"
        exit 1
    fi
    
    log_message "${GREEN}✅ Docker Compose is available${NC}"
}

# Function to backup current state
backup_current_state() {
    log_message "${YELLOW}📦 Creating backup of current state...${NC}"
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup Docker volumes
    log_message "${BLUE}📋 Backing up Docker volumes...${NC}"
    docker run --rm -v asimnexus_postgres_data:/data -v "$BACKUP_DIR":/backup alpine tar czf /backup/postgres_data.tar.gz -C /data .
    docker run --rm -v asimnexus_redis_data:/data -v "$BACKUP_DIR":/backup alpine tar czf /backup/redis_data.tar.gz -C /data .
    docker run --rm -v asimnexus_model_cache:/data -v "$BACKUP_DIR":/backup alpine tar czf /backup/model_cache.tar.gz -C /data .
    
    # Backup configuration files
    cp .env "$BACKUP_DIR/" 2>/dev/null || true
    cp "$DOCKER_COMPOSE_FILE" "$BACKUP_DIR/" 2>/dev/null || true
    cp -r ./data "$BACKUP_DIR/" 2>/dev/null || true
    
    log_message "${GREEN}✅ Backup created at: $BACKUP_DIR${NC}"
}

# Function to check Git status
check_git_status() {
    log_message "${YELLOW}🔍 Checking Git repository status...${NC}"
    
    if [ ! -d ".git" ]; then
        log_message "${RED}❌ Not a Git repository${NC}"
        exit 1
    fi
    
    # Get current branch
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    log_message "${BLUE}🌿 Current branch: $CURRENT_BRANCH${NC}"
    
    # Check for uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        log_message "${YELLOW}⚠️  Uncommitted changes detected${NC}"
        log_message "${BLUE}💾 Stashing changes...${NC}"
        git stash push -m "Auto-update stash $(date)" >> "$LOG_FILE" 2>&1
    fi
    
    log_message "${GREEN}✅ Git repository is clean${NC}"
}

# Function to pull latest changes
pull_latest_changes() {
    log_message "${YELLOW}📥 Pulling latest changes from $BRANCH branch...${NC}"
    
    # Fetch latest changes
    git fetch origin "$BRANCH" >> "$LOG_FILE" 2>&1
    
    # Check if there are new changes
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/"$BRANCH")
    
    if [ "$LOCAL" = "$REMOTE" ]; then
        log_message "${GREEN}✅ Already up to date${NC}"
        return 0
    fi
    
    log_message "${BLUE}🔄 New changes detected, pulling...${NC}"
    git pull origin "$BRANCH" >> "$LOG_FILE" 2>&1
    
    log_message "${GREEN}✅ Latest changes pulled successfully${NC}"
}

# Function to install/update dependencies
update_dependencies() {
    log_message "${YELLOW}📦 Updating dependencies...${NC}"
    
    # Update Python dependencies
    if [ -f "requirements.txt" ]; then
        log_message "${BLUE}🐍 Updating Python dependencies...${NC}"
        pip install -r requirements.txt >> "$LOG_FILE" 2>&1
    fi
    
    # Update Node.js dependencies
    if [ -f "interface/web/package.json" ]; then
        log_message "${BLUE}📱 Updating Node.js dependencies...${NC}"
        cd interface/web
        npm install >> "../../$LOG_FILE" 2>&1
        cd ..
    fi
    
    log_message "${GREEN}✅ Dependencies updated${NC}"
}

# Function to build Docker images
build_docker_images() {
    log_message "${YELLOW}🐳 Building Docker images...${NC}"
    
    # Build backend image
    log_message "${BLUE}🔧 Building backend image...${NC}"
    docker build -t asimnexus/backend:latest . >> "$LOG_FILE" 2>&1
    
    # Build frontend image
    if [ -f "interface/web/Dockerfile" ]; then
        log_message "${BLUE}🎨 Building frontend image...${NC}"
        docker build -t asimnexus/frontend:latest ./interface/web >> "$LOG_FILE" 2>&1
    fi
    
    # Build agent images
    log_message "${BLUE}🤖 Building agent images...${NC}"
    docker build -t asimnexus/system-optimizer:latest --target agent . >> "$LOG_FILE" 2>&1
    docker build -t asimnexus/screen-analyst:latest --target agent . >> "$LOG_FILE" 2>&1
    docker build -t asimnexus/sandbox-executor:latest --target agent . >> "$LOG_FILE" 2>&1
    docker build -t asimnexus/rtx-stress-adaptor:latest --target agent . >> "$LOG_FILE" 2>&1
    
    log_message "${GREEN}✅ Docker images built successfully${NC}"
}

# Function to stop services
stop_services() {
    log_message "${YELLOW}🛑 Stopping ASIMNEXUS services...${NC}"
    
    # Stop all services using Docker Compose
    if [ -f "$DOCKER_COMPOSE_FILE" ]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" down >> "$LOG_FILE" 2>&1
    fi
    
    # Wait for services to stop
    sleep 5
    
    log_message "${GREEN}✅ Services stopped${NC}"
}

# Function to start services
start_services() {
    log_message "${YELLOW}🚀 Starting ASIMNEXUS services...${NC}"
    
    # Start services using Docker Compose
    if [ -f "$DOCKER_COMPOSE_FILE" ]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d >> "$LOG_FILE" 2>&1
    fi
    
    # Wait for services to start
    log_message "${BLUE}⏳ Waiting for services to initialize...${NC}"
    sleep 30
    
    log_message "${GREEN}✅ Services started${NC}"
}

# Function to verify services
verify_services() {
    log_message "${YELLOW}🔍 Verifying service health...${NC}"
    
    # Check if backend is responding
    if curl -f http://localhost:8000/api/health >> "$LOG_FILE" 2>&1; then
        log_message "${GREEN}✅ Backend service is healthy${NC}"
    else
        log_message "${RED}❌ Backend service is not responding${NC}"
        return 1
    fi
    
    # Check if frontend is responding
    if curl -f http://localhost:3000 >> "$LOG_FILE" 2>&1; then
        log_message "${GREEN}✅ Frontend service is healthy${NC}"
    else
        log_message "${RED}❌ Frontend service is not responding${NC}"
        return 1
    fi
    
    # Check Docker containers
    RUNNING_CONTAINERS=$(docker ps --format "table {{.Names}}" | grep asimnexus | wc -l)
    log_message "${BLUE}📊 Running containers: $RUNNING_CONTAINERS${NC}"
    
    log_message "${GREEN}✅ All services verified${NC}"
}

# Function to cleanup old images
cleanup_old_images() {
    log_message "${YELLOW}🧹 Cleaning up old Docker images...${NC}"
    
    # Remove dangling images
    docker image prune -f >> "$LOG_FILE" 2>&1
    
    # Remove old ASIMNEXUS images (keep last 3 versions)
    docker images --format "table {{.Repository}}:{{.Tag}}" | grep asimnexus | tail -n +4 | awk '{print $1":"$2}' | xargs -r docker rmi >> "$LOG_FILE" 2>&1 || true
    
    log_message "${GREEN}✅ Cleanup completed${NC}"
}

# Function to restore backup on failure
restore_backup() {
    log_message "${RED}🚨 Update failed, restoring backup...${NC}"
    
    # Stop services
    docker-compose -f "$DOCKER_COMPOSE_FILE" down >> "$LOG_FILE" 2>&1 || true
    
    # Restore Docker volumes
    if [ -f "$BACKUP_DIR/postgres_data.tar.gz" ]; then
        docker run --rm -v asimnexus_postgres_data:/data -v "$BACKUP_DIR":/backup alpine tar xzf /backup/postgres_data.tar.gz -C /data
    fi
    
    if [ -f "$BACKUP_DIR/redis_data.tar.gz" ]; then
        docker run --rm -v asimnexus_redis_data:/data -v "$BACKUP_DIR":/backup alpine tar xzf /backup/redis_data.tar.gz -C /data
    fi
    
    if [ -f "$BACKUP_DIR/model_cache.tar.gz" ]; then
        docker run --rm -v asimnexus_model_cache:/data -v "$BACKUP_DIR":/backup alpine tar xzf /backup/model_cache.tar.gz -C /data
    fi
    
    # Restore configuration
    cp "$BACKUP_DIR/.env" ./ 2>/dev/null || true
    
    # Restart services
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d >> "$LOG_FILE" 2>&1
    
    log_message "${GREEN}✅ Backup restored${NC}"
}

# Function to send notification (optional)
send_notification() {
    local status=$1
    local message=$2
    
    # You can implement webhook notifications here
    # Example: curl -X POST -H 'Content-type: application/json' --data '{"text":"ASIMNEXUS Update: '$status' - '$message'"}' YOUR_WEBHOOK_URL
    
    log_message "${PURPLE}📢 Update $status: $message${NC}"
}

# Main update function
main_update() {
    log_message "${CYAN}🚀 Starting ASIMNEXUS update process...${NC}"
    
    # Pre-update checks
    check_root
    check_docker
    check_docker_compose
    check_git_status
    
    # Create backup
    backup_current_state
    
    # Update process
    trap 'log_message "${RED}❌ Update failed, restoring backup...${NC}"; restore_backup; send_notification "FAILED" "Update process failed"; exit 1' ERR
    
    pull_latest_changes
    update_dependencies
    build_docker_images
    stop_services
    start_services
    verify_services
    cleanup_old_images
    
    # Remove trap on success
    trap - ERR
    
    log_message "${GREEN}🎉 ASIMNEXUS update completed successfully!${NC}"
    send_notification "SUCCESS" "ASIMNEXUS updated and running"
}

# Function to show help
show_help() {
    echo -e "${CYAN}ASIMNEXUS Self-Update Engine${NC}"
    echo -e "${CYAN}============================${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -b, --backup-only   Create backup only"
    echo "  -r, --restore       Restore from latest backup"
    echo "  -s, --status        Show current status"
    echo "  -c, --check         Check for updates without applying"
    echo "  -f, --force         Force update even if up to date"
    echo ""
    echo "Examples:"
    echo "  $0                  # Run full update"
    echo "  $0 --backup-only    # Create backup only"
    echo "  $0 --restore        # Restore from backup"
    echo "  $0 --status         # Show current status"
    echo "  $0 --check          # Check for updates"
    echo ""
}

# Function to check for updates only
check_updates() {
    log_message "${YELLOW}🔍 Checking for updates...${NC}"
    
    git fetch origin "$BRANCH" >> "$LOG_FILE" 2>&1
    
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/"$BRANCH")
    
    if [ "$LOCAL" = "$REMOTE" ]; then
        log_message "${GREEN}✅ ASIMNEXUS is up to date${NC}"
        return 0
    else
        log_message "${YELLOW}📥 Updates are available${NC}"
        log_message "${BLUE}📊 Local:  ${LOCAL:0:8}...${NC}"
        log_message "${BLUE}📊 Remote: ${REMOTE:0:8}...${NC}"
        return 1
    fi
}

# Function to show status
show_status() {
    echo -e "${CYAN}ASIMNEXUS Status${NC}"
    echo -e "${CYAN}================${NC}"
    echo ""
    
    # Git status
    echo -e "${BLUE}📂 Repository Status:${NC}"
    git status --porcelain | head -5
    echo ""
    
    # Docker status
    echo -e "${BLUE}🐳 Docker Status:${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep asimnexus || echo "No ASIMNEXUS containers running"
    echo ""
    
    # Service health
    echo -e "${BLUE}🏥 Service Health:${NC}"
    if curl -s http://localhost:8000/api/health > /dev/null; then
        echo -e "${GREEN}✅ Backend: Healthy${NC}"
    else
        echo -e "${RED}❌ Backend: Unhealthy${NC}"
    fi
    
    if curl -s http://localhost:3000 > /dev/null; then
        echo -e "${GREEN}✅ Frontend: Healthy${NC}"
    else
        echo -e "${RED}❌ Frontend: Unhealthy${NC}"
    fi
    echo ""
    
    # System resources
    echo -e "${BLUE}💻 System Resources:${NC}"
    echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
    echo "Memory: $(free -h | awk '/^Mem:/ {print $3 "/" $2}')"
    echo "Disk: $(df -h . | awk 'NR==2 {print $3 "/" $2 " (" $5 ")"}')"
    echo ""
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    -b|--backup-only)
        check_docker
        backup_current_state
        log_message "${GREEN}✅ Backup completed${NC}"
        exit 0
        ;;
    -r|--restore)
        LATEST_BACKUP=$(ls -t ./backups/ | head -1)
        if [ -z "$LATEST_BACKUP" ]; then
            log_message "${RED}❌ No backup found${NC}"
            exit 1
        fi
        BACKUP_DIR="./backups/$LATEST_BACKUP"
        restore_backup
        exit 0
        ;;
    -s|--status)
        show_status
        exit 0
        ;;
    -c|--check)
        check_docker
        check_git_status
        check_updates
        exit 0
        ;;
    -f|--force)
        log_message "${YELLOW}⚡ Force update mode enabled${NC}"
        main_update
        ;;
    "")
        main_update
        ;;
    *)
        log_message "${RED}❌ Unknown option: $1${NC}"
        show_help
        exit 1
        ;;
esac

# Final status
echo ""
echo -e "${GREEN}🎉 ASIMNEXUS Self-Update Engine completed!${NC}"
echo -e "${BLUE}📅 Completed at: $(date)${NC}"
echo -e "${BLUE}📝 Log file: $LOG_FILE${NC}"
echo ""
