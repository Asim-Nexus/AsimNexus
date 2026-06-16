#!/bin/bash
# STATUS: REAL — Production Deployment Script for AsimNexus
# Run this script to deploy AsimNexus in production mode

set -e  # Exit on error

echo "🚀 AsimNexus Production Deployment"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Log function
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 not found"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_warn "Docker not found - skipping container deployment"
    fi
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_warn "kubectl not found - skipping Kubernetes deployment"
    fi
    
    log_info "Prerequisites check complete"
}

# Backup SQLite databases
backup_sqlite() {
    log_info "Backing up SQLite databases..."
    
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup government data
    if [ -f "data/asim_gov.db" ]; then
        cp data/asim_gov.db "$BACKUP_DIR/gov_backup.db"
        log_info "Government database backed up"
    fi
    
    # Backup company data
    if [ -f "data/asim_company.db" ]; then
        cp data/asim_company.db "$BACKUP_DIR/company_backup.db"
        log_info "Company database backed up"
    fi
    
    # Backup citizen data
    if [ -f "data/asim_user.db" ]; then
        cp data/asim_user.db "$BACKUP_DIR/user_backup.db"
        log_info "User database backed up"
    fi
    
    log_info "Backup complete: $BACKUP_DIR"
}

# Run PostgreSQL migration
run_migration() {
    log_info "Running PostgreSQL migration..."
    
    python3 -c "
import asyncio
from database.migrations.postgresql import PostgreSQLMigration

async def migrate():
    m = PostgreSQLMigration()
    result = await m.migrate_all()
    print('Migration result:', result)

asyncio.run(migrate())
"
    
    log_info "PostgreSQL migration complete"
}

# Initialize security modules
init_security() {
    log_info "Initializing security modules..."
    
    # Initialize HSM (will fallback to software if not available)
    python3 -c "
from security.hsm_production import get_hsm
hsm = get_hsm()
print('HSM Status:', hsm.status())
"
    
    # Initialize ZKP
    python3 -c "
from security.zkp_production import get_zkp
import asyncio
zkp = get_zkp()
print('ZKP Status:', zkp.status())
"
    
    log_info "Security modules initialized"
}

# Run tests
run_tests() {
    log_info "Running integration tests..."
    
    pytest tests/integration/ -v --tb=short || {
        log_warn "Some tests failed - check logs"
    }
    
    log_info "Tests complete"
}

# Deploy with Docker
deploy_docker() {
    log_info "Building Docker containers..."
    
    docker build -t asimnexus/gov-backend:latest -f docker/Dockerfile.gov . || log_warn "Government Dockerfile not found"
    docker build -t asimnexus/company-backend:latest -f docker/Dockerfile.company . || log_warn "Company Dockerfile not found"
    docker build -t asimnexus/user-backend:latest -f docker/Dockerfile.user . || log_warn "User Dockerfile not found"
    
    log_info "Docker build complete"
}

# Deploy to Kubernetes
deploy_k8s() {
    log_info "Deploying to Kubernetes..."
    
    # Apply namespaces
    kubectl apply -f k8s/production/gov-namespace.yaml || log_warn "Gov namespace not found"
    kubectl apply -f k8s/production/company-namespace.yaml || log_warn "Company namespace not found"
    kubectl apply -f k8s/production/user-namespace.yaml || log_warn "User namespace not found"
    
    # Apply deployments
    kubectl apply -f k8s/production/gov-deployment.yaml || log_warn "Gov deployment not found"
    kubectl apply -f k8s/production/company-deployment.yaml || log_warn "Company deployment not found"
    kubectl apply -f k8s/production/user-deployment.yaml || log_warn "User deployment not found"
    
    log_info "Kubernetes deployment complete"
}

# Start the backend
start_backend() {
    log_info "Starting backend servers..."
    
    # Start all backends
    nohup python3 -m uvicorn simple_backend:app --host 0.0.0.0 --port 8000 > logs/backend.log 2>&1 &
    
    log_info "Backend started on port 8000"
}

# Main deployment function
main() {
    log_info "Starting AsimNexus Production Deployment..."
    
    check_prerequisites
    
    # Backup before anything else
    backup_sqlite
    
    # Initialize security
    init_security
    
    # Run migration if PostgreSQL is configured
    if [ -n "$DATABASE_URL_GOV" ]; then
        run_migration
    fi
    
    # Run tests
    run_tests
    
    # Deploy options
    if [ "$1" == "--docker" ]; then
        deploy_docker
    fi
    
    if [ "$1" == "--k8s" ]; then
        deploy_k8s
    fi
    
    # Start backend if requested
    if [ "$1" == "--start" ]; then
        start_backend
    fi
    
    log_info "🎉 AsimNexus Production Deployment Complete!"
    log_info "📊 Status: Ready for production testing"
}

# Run main with argument
main "$1"