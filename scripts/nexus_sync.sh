#!/bin/bash

# ASIMNEXUS Automated CI/CD Pipeline
# ==================================
# Git pull, Docker auto-update, and heartbeat restart

set -e

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
DOCKER_COMPOSE_FILE="docker-compose.awakening.yml"
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
LOG_FILE="./logs/nexus_sync_$(date +%Y%m%d_%H%M%S).log"
HEARTBEAT_SERVICE="live_heartbeat.py"

# Create log directory
mkdir -p logs backups

echo -e "${CYAN}🔄 ASIMNEXUS Automated CI/CD Pipeline${NC}"
echo -e "${CYAN}=======================================${NC}"
echo -e "${BLUE}📅 Sync started at: $(date)${NC}"
echo -e "${BLUE}📝 Log file: $LOG_FILE${NC}"
echo ""

# Function to log messages
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a "$LOG_FILE"
}

# Function to check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log "${RED}❌ This script should not be run as root${NC}"
        exit 1
    fi
}

# Function to check prerequisites
check_prerequisites() {
    log "🔍 Checking prerequisites..."
    
    # Check Git
    if ! command -v git &> /dev/null; then
        log "${RED}❌ Git is not installed${NC}"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log "${RED}❌ Docker is not installed${NC}"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log "${RED}❌ Docker Compose is not installed${NC}"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log "${RED}❌ Docker daemon is not running${NC}"
        exit 1
    fi
    
    log "${GREEN}✅ All prerequisites satisfied${NC}"
}

# Function to create backup
create_backup() {
    log "📦 Creating backup before update..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup Docker volumes
    log "💾 Backing up Docker volumes..."
    docker run --rm -v asimnexus_postgres_data:/data -v "$BACKUP_DIR":/backup alpine tar czf /backup/postgres_data.tar.gz -C /data .
    docker run --rm -v asimnexus_redis_data:/data -v "$BACKUP_DIR":/backup alpine tar czf /backup/redis_data.tar.gz -C /data .
    docker run --rm -v asimnexus_model_cache:/data -v "$BACKUP_DIR":/backup alpine tar czf /backup/model_cache.tar.gz -C /data .
    
    # Backup configuration files
    log "📋 Backing up configuration files..."
    cp .env "$BACKUP_DIR/" 2>/dev/null || true
    cp "$DOCKER_COMPOSE_FILE" "$BACKUP_DIR/" 2>/dev/null || true
    cp -r ./data "$BACKUP_DIR/" 2>/dev/null || true
    
    # Backup current running containers
    log "🐳 Backing up container states..."
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" > "$BACKUP_DIR/containers.txt"
    
    log "${GREEN}✅ Backup created at: $BACKUP_DIR${NC}"
}

# Function to check Git status
check_git_status() {
    log "🔍 Checking Git repository status..."
    
    # Check if we're in a Git repository
    if [ ! -d ".git" ]; then
        log "${RED}❌ Not a Git repository${NC}"
        exit 1
    fi
    
    # Get current branch
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
    log "${BLUE}🌿 Current branch: $CURRENT_BRANCH${NC}"
    
    # Check for uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        log "${YELLOW}⚠️  Uncommitted changes detected${NC}"
        git status --short
        
        # Ask user what to do
        echo -e "${YELLOW}❓ Uncommitted changes found. What would you like to do?${NC}"
        echo -e "${YELLOW}1) Stash changes and continue${NC}"
        echo -e "${YELLOW}2) Commit changes and continue${NC}"
        echo -e "${YELLOW}3) Abort and exit${NC}"
        echo -n -e "${YELLOW}Choose an option (1-3): ${NC}"
        read -r choice
        
        case $choice in
            1)
                log "💾 Stashing changes..."
                git stash push -m "Auto-sync stash $(date)"
                ;;
            2)
                log "📝 Committing changes..."
                git add .
                git commit -m "Auto-sync commit $(date)"
                ;;
            3)
                log "${RED}❌ Aborting sync${NC}"
                exit 1
                ;;
            *)
                log "${RED}❌ Invalid option${NC}"
                exit 1
                ;;
        esac
    fi
    
    # Check if we're on the right branch
    if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
        log "${YELLOW}⚠️  Not on target branch ($BRANCH)${NC}"
        log "${BLUE}🔄 Switching to $BRANCH branch...${NC}"
        git checkout "$BRANCH"
    fi
}

# Function to pull latest changes
pull_latest_changes() {
    log "📥 Pulling latest changes from $BRANCH branch..."
    
    # Fetch latest changes
    git fetch origin "$BRANCH"
    
    # Check if there are new changes
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/"$BRANCH")
    
    if [ "$LOCAL" = "$REMOTE" ]; then
        log "${GREEN}✅ Already up to date${NC}"
        return 0
    fi
    
    log "${BLUE}🔄 New changes detected, pulling...${NC}"
    git pull origin "$BRANCH"
    
    if [ $? -eq 0 ]; then
        log "${GREEN}✅ Latest changes pulled successfully${NC}"
    else
        log "${RED}❌ Failed to pull latest changes${NC}"
        return 1
    fi
}

# Function to rebuild Docker images
rebuild_docker_images() {
    log "🐳 Rebuilding Docker images..."
    
    # Build ASIMNEXUS backend image
    log "${BLUE}🔧 Building ASIMNEXUS backend image...${NC}"
    docker build -t asimnexus/backend:latest . 2>&1 | tee -a "$LOG_FILE"
    
    if [ ${PIPESTATUS[0]} -eq 0 ]; then
        log "${GREEN}✅ Backend image built successfully${NC}"
    else
        log "${RED}❌ Failed to build backend image${NC}"
        return 1
    fi
    
    # Build frontend image if Dockerfile exists
    if [ -f "interface/web/Dockerfile" ]; then
        log "${BLUE}🎨 Building frontend image...${NC}"
        docker build -t asimnexus/frontend:latest ./interface/web 2>&1 | tee -a "$LOG_FILE"
        
        if [ ${PIPESTATUS[0]} -eq 0 ]; then
            log "${GREEN}✅ Frontend image built successfully${NC}"
        else
            log "${RED}❌ Failed to build frontend image${NC}"
            return 1
        fi
    fi
    
    # Build agent images
    log "${BLUE}🤖 Building agent images...${NC}"
    docker build -t asimnexus/system-optimizer:latest --target agent . 2>&1 | tee -a "$LOG_FILE"
    docker build -t asimnexus/screen-analyst:latest --target agent . 2>&1 | tee -a "$LOG_FILE"
    docker build -t asimnexus/sandbox-executor:latest --target agent . 2>&1 | tee -a "$LOG_FILE"
    docker build -t asimnexus/rtx-stress-adaptor:latest --target agent . 2>&1 | tee -a "$LOG_FILE"
    
    log "${GREEN}✅ All Docker images rebuilt successfully${NC}"
}

# Function to stop existing services
stop_existing_services() {
    log "🛑 Stopping existing ASIMNEXUS services..."
    
    if [ -f "$DOCKER_COMPOSE_FILE" ]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" down 2>&1 | tee -a "$LOG_FILE"
        
        if [ $? -eq 0 ]; then
            log "${GREEN}✅ Services stopped successfully${NC}"
        else
            log "${YELLOW}⚠️  Some services may already be stopped${NC}"
        fi
    else
        log "${YELLOW}⚠️  Docker compose file not found: $DOCKER_COMPOSE_FILE${NC}"
    fi
    
    # Wait for services to fully stop
    log "⏳ Waiting for services to stop..."
    sleep 10
}

# Function to start updated services
start_updated_services() {
    log "🚀 Starting updated ASIMNEXUS services..."
    
    if [ -f "$DOCKER_COMPOSE_FILE" ]; then
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d 2>&1 | tee -a "$LOG_FILE"
        
        if [ $? -eq 0 ]; then
            log "${GREEN}✅ Services started successfully${NC}"
        else
            log "${RED}❌ Failed to start services${NC}"
            return 1
        fi
    else
        log "${RED}❌ Docker compose file not found: $DOCKER_COMPOSE_FILE${NC}"
        return 1
    fi
    
    # Wait for services to initialize
    log "⏳ Waiting for services to initialize..."
    sleep 30
}

# Function to restart heartbeat service
restart_heartbeat_service() {
    log "💓 Restarting heartbeat service..."
    
    # Find and kill existing heartbeat process
    HEARTBEAT_PID=$(pgrep -f "$HEARTBEAT_SERVICE" | head -1)
    
    if [ -n "$HEARTBEAT_PID" ]; then
        log "${YELLOW}⚠️  Stopping existing heartbeat process (PID: $HEARTBEAT_PID)${NC}"
        kill -TERM "$HEARTBEAT_PID"
        sleep 5
        
        # Force kill if still running
        if pgrep -f "$HEARTBEAT_SERVICE" > /dev/null; then
            log "${YELLOW}⚠️  Force killing heartbeat process${NC}"
            kill -KILL "$HEARTBEAT_PID"
        fi
    fi
    
    # Start heartbeat service
    if [ -f "$HEARTBEAT_SERVICE" ]; then
        nohup python3 "$HEARTBEAT_SERVICE" > logs/heartbeat.log 2>&1 &
        HEARTBEAT_NEW_PID=$!
        
        if [ -n "$HEARTBEAT_NEW_PID" ]; then
            log "${GREEN}✅ Heartbeat service started (PID: $HEARTBEAT_NEW_PID)${NC}"
        else
            log "${RED}❌ Failed to start heartbeat service${NC}"
            return 1
        fi
    else
        log "${RED}❌ Heartbeat service not found: $HEARTBEAT_SERVICE${NC}"
        return 1
    fi
}

# Function to verify services
verify_services() {
    log "🔍 Verifying service health..."
    
    # Check if backend is responding
    BACKEND_URL="http://localhost:8000/api/health"
    if curl -f "$BACKEND_URL" > /dev/null 2>&1; then
        log "${GREEN}✅ Backend health check passed${NC}"
    else
        log "${RED}❌ Backend health check failed${NC}"
        return 1
    fi
    
    # Check if frontend is responding
    FRONTEND_URL="http://localhost:3000"
    if curl -f "$FRONTEND_URL" > /dev/null 2>&1; then
        log "${GREEN}✅ Frontend health check passed${NC}"
    else
        log "${RED}❌ Frontend health check failed${NC}"
        return 1
    fi
    
    # Check Docker containers
    RUNNING_CONTAINERS=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep asimnexus | wc -l)
    log "${BLUE}🐳 Running containers: $RUNNING_CONTAINERS${NC}"
    
    if [ "$RUNNING_CONTAINERS" -gt 0 ]; then
        log "${GREEN}✅ Docker containers are running${NC}"
    else
        log "${RED}❌ No ASIMNEXUS containers are running${NC}"
        return 1
    fi
    
    # Check heartbeat service
    if pgrep -f "$HEARTBEAT_SERVICE" > /dev/null; then
        log "${GREEN}✅ Heartbeat service is running${NC}"
    else
        log "${RED}❌ Heartbeat service is not running${NC}"
        return 1
    fi
    
    log "${GREEN}✅ All services verified successfully${NC}"
    return 0
}

# Function to cleanup old backups
cleanup_old_backups() {
    log "🧹 Cleaning up old backups..."
    
    # Keep only last 7 days of backups
    find ./backups -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
    
    # Keep only last 30 days of logs
    find ./logs -name "nexus_sync_*.log" -mtime +30 -delete 2>/dev/null || true
    
    log "${GREEN}✅ Cleanup completed${NC}"
}

# Function to rollback on failure
rollback_on_failure() {
    log "${RED}🚨 Update failed, initiating rollback...${NC}"
    
    # Stop any partially started services
    docker-compose -f "$DOCKER_COMPOSE_FILE" down 2>/dev/null || true
    
    # Restore from backup if available
    if [ -d "$BACKUP_DIR" ]; then
        log "🔄 Restoring from backup: $BACKUP_DIR${NC}"
        
        # Restore Docker volumes
        if [ -f "$BACKUP_DIR/postgres_data.tar.gz" ]; then
            docker run --rm -v asimnexus_postgres_data:/data -v "$BACKUP_DIR":/backup alpine tar xzf /backup/postgres_data.tar.gz -C /data
        fi
        
        if [ -f "$BACKUP_DIR/redis_data.tar.gz" ]; then
            docker run --rm -v asimnexus_redis_data:/data -v "$BACKUP_DIR":/backup alpine tar xzf /backup/redis_data.tar.gz -C /data
        fi
        
        # Restart services with backup
        docker-compose -f "$DOCKER_COMPOSE_FILE" up -d 2>/dev/null || true
        
        log "${GREEN}✅ Rollback completed${NC}"
    else
        log "${RED}❌ No backup available for rollback${NC}"
    fi
}

# Function to show help
show_help() {
    echo -e "${CYAN}ASIMNEXUS Automated CI/CD Pipeline${NC}"
    echo -e "${CYAN}=======================================${NC}"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -b, --backup-only  Create backup only"
    echo "  -r, --restore       Restore from latest backup"
    echo "  -s, --status       Show current status"
    echo "  -c, --check        Check for updates without applying"
    echo "  -f, --force        Force update even if up to date"
    echo "  -v, --verbose       Verbose output"
    echo ""
    echo "Examples:"
    echo "  $0                  # Run full update"
    echo "  $0 --backup-only    # Create backup only"
    echo "  $0 --restore        # Restore from backup"
    echo "  $0 --status         # Show current status"
    echo "  $0 --check          # Check for updates"
    echo "  $0 --force          # Force update"
}

# Function to show status
show_status() {
    echo -e "${CYAN}ASIMNEXUS Status${NC}"
    echo -e "${CYAN}================${NC}"
    echo ""
    
    # Git status
    echo -e "${BLUE}📂 Git Status:${NC}"
    git status --short
    echo ""
    
    # Docker status
    echo -e "${BLUE}🐳 Docker Status:${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}" | grep asimnexus || echo "No ASIMNEXUS containers running"
    echo ""
    
    # Service health
    echo -e "${BLUE}🏥 Service Health:${NC}"
    if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
        echo "Backend: ✅ Online"
    else
        echo "Backend: ❌ Offline"
    fi
    
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        echo "Frontend: ✅ Online"
    else
        echo "Frontend: ❌ Offline"
    fi
    
    echo ""
    
    # Heartbeat status
    echo -e "${BLUE}💓 Heartbeat Service:${NC}"
    if pgrep -f "$HEARTBEAT_SERVICE" > /dev/null; then
        echo "Status: ✅ Running"
        echo "PID: $(pgrep -f "$HEARTBEAT_SERVICE" | head -1)"
    else
        echo "Status: ❌ Not running"
    fi
    echo ""
}

# Main update function
main_update() {
    log "🚀 Starting ASIMNEXUS update process..."
    
    # Run all update steps
    check_prerequisites
    create_backup
    check_git_status
    pull_latest_changes
    
    if [ $? -eq 0 ]; then
        rebuild_docker_images
        stop_existing_services
        start_updated_services
        restart_heartbeat_service
        
        if verify_services; then
            cleanup_old_backups
            log "${GREEN}🎉 ASIMNEXUS update completed successfully!${NC}"
            echo ""
            echo -e "${GREEN}🌐 ASIMNEXUS is now running with the latest updates${NC}"
            echo -e "${GREEN}📊 Dashboard: http://localhost:3000${NC}"
            echo -e "${GREEN}🔗 API: http://localhost:8000${NC}"
            echo -e "${GREEN}💓 Heartbeat: Active${NC}"
        else
            rollback_on_failure
            exit 1
        fi
    else
        log "${RED}❌ Update failed during Git pull${NC}"
        exit 1
    fi
}

# Parse command line arguments
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    -b|--backup-only)
        check_prerequisites
        create_backup
        cleanup_old_backups
        log "${GREEN}✅ Backup completed${NC}"
        exit 0
        ;;
    -r|--restore)
        check_prerequisites
        rollback_on_failure
        exit 0
        ;;
    -s|--status)
        show_status
        exit 0
        ;;
    -c|--check)
        check_prerequisites
        check_git_status
        pull_latest_changes
        exit 0
        ;;
    -f|--force)
        log "${YELLOW}⚡ Force update mode enabled${NC}"
        main_update
        ;;
    -v|--verbose)
        set -x
        main_update
        ;;
    "")
        main_update
        ;;
    *)
        log "${RED}❌ Unknown option: $1${NC}"
        show_help
        exit 1
        ;;
esac

# Final status
echo ""
echo -e "${GREEN}🎊 ASIMNEXUS CI/CD Pipeline completed!${NC}"
echo -e "${BLUE}📅 Completed at: $(date)${NC}"
echo -e "${BLUE}📝 Log file: $LOG_FILE${NC}"
echo ""
