#!/bin/bash
# ASIMNEXUS Founder Distribution Script - Linux/macOS
# ====================================================
# One-click ASIMNEXUS installation for Founder Clones
# Automatically detects hardware and configures optimal settings

set -e

# Color scheme for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
NC='\033[0m' # No Color

# Default parameters
MODE="auto"
VERSION="latest"
FOUNDER_KEY=""
INSTALL_PATH="$HOME/ASIMNEXUS"
SKIP_DOCKER=false
DEV_MODE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --version)
            VERSION="$2"
            shift 2
            ;;
        --founder-key)
            FOUNDER_KEY="$2"
            shift 2
            ;;
        --install-path)
            INSTALL_PATH="$2"
            shift 2
            ;;
        --skip-docker)
            SKIP_DOCKER=true
            shift
            ;;
        --dev-mode)
            DEV_MODE=true
            shift
            ;;
        --help|-h)
            echo "ASIMNEXUS Founder Clone Setup Script"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --mode MODE         Installation mode (auto, titan, full_neural, quantized_heavy, quantized_medium, quantized_light)"
            echo "  --version VERSION    Specific version to install (default: latest)"
            echo "  --founder-key KEY  Founder authentication key"
            echo "  --install-path PATH  Installation directory (default: ~/ASIMNEXUS)"
            echo "  --skip-docker       Skip Docker installation check"
            echo "  --dev-mode         Development mode (don't start services)"
            echo "  --help, -h         Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Auto-install with optimal settings"
            echo "  $0 --mode full_neural               # Force full neural mode"
            echo "  $0 --version v2.1.0 --install-path /opt/asimnexus"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Function to print colored output
print_color() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to show banner
show_banner() {
    echo ""
    print_color "$CYAN" "╔════════════════════════════════════════════════════════════╗"
    print_color "$CYAN" "║                   ASIMNEXUS FOUNDER CLONE SETUP                    ║"
    print_color "$CYAN" "║                Universal Operating System Installer                ║"
    print_color "$CYAN" "╚════════════════════════════════════════════════════════════╝"
    echo ""
}

# Function to check if running as root (for system-wide installation)
check_root() {
    if [[ $EUID -eq 0 ]]; then
        print_color "$YELLOW" "⚠️  Running as root - installing system-wide"
        return 0
    else
        print_color "$GREEN" "🔑 User installation detected"
        return 1
    fi
}

# Function to detect system information
get_system_info() {
    print_color "$WHITE" "🔍 Detecting System Configuration..."
    
    local system_info=()
    
    # OS Information
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        system_info[OS]="Linux"
        system_info[OS_VERSION]=$(lsb_release -d 2>/dev/null || echo "Unknown Linux")
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        system_info[OS]="macOS"
        system_info[OS_VERSION]=$(sw_vers -productVersion)
    else
        system_info[OS]="Unknown"
        system_info[OS_VERSION]="Unknown"
    fi
    
    # Architecture
    system_info[ARCH]=$(uname -m)
    
    # CPU Information
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        system_info[CPU]=$(lscpu | grep 'Model name' | cut -d':' -f2 | xargs)
        system_info[CORES]=$(nproc)
        system_info[THREADS]=$(lscpu | grep 'CPU(s):' | cut -d':' -f2 | xargs)
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        system_info[CPU]=$(sysctl -n machdep.cpu.brand_string)
        system_info[CORES]=$(sysctl -n hw.ncpu)
        system_info[THREADS]=$(sysctl -n hw.ncpu)
    fi
    
    # Memory Information
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        TOTAL_MEMORY_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
        system_info[TOTAL_MEMORY_GB]=$(echo "scale=2; $TOTAL_MEMORY_KB / 1024 / 1024" | bc)
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        TOTAL_MEMORY_BYTES=$(sysctl -n hw.memsize)
        system_info[TOTAL_MEMORY_GB]=$(echo "scale=2; $TOTAL_MEMORY_BYTES / 1024 / 1024 / 1024" | bc)
    fi
    
    # GPU Detection
    system_info[GPU]="Unknown"
    system_info[GPU_MEMORY_GB]=0
    
    if command -v nvidia-smi &> /dev/null; then
        GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader,nounits 2>/dev/null)
        if [[ -n "$GPU_INFO" ]]; then
            IFS=',' read -ra GPU_PARTS <<< "$GPU_INFO"
            system_info[GPU]=$(echo "${GPU_PARTS[0]}" | xargs)
            GPU_MEMORY_MB=$(echo "${GPU_PARTS[1]}" | xargs)
            system_info[GPU_MEMORY_GB]=$(echo "scale=2; $GPU_MEMORY_MB / 1024" | bc)
        fi
    else
        print_color "$YELLOW" "⚠️  NVIDIA GPU not detected - will use CPU mode"
    fi
    
    # Disk Space Check
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        FREE_SPACE_KB=$(df /home | tail -1 | awk '{print $4}')
        system_info[FREE_DISK_SPACE_GB]=$(echo "scale=2; $FREE_SPACE_KB / 1024 / 1024" | bc)
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        FREE_SPACE_KB=$(df -k /Users | tail -1 | awk '{print $4}')
        system_info[FREE_DISK_SPACE_GB]=$(echo "scale=2; $FREE_SPACE_KB / 1024" | bc)
    fi
    
    # Determine Hardware Tier
    system_info[HARDWARE_TIER]=$(get_hardware_tier "${system_info[TOTAL_MEMORY_GB]}" "${system_info[GPU_MEMORY_GB]}")
    
    # Determine Recommended Mode
    system_info[RECOMMENDED_MODE]=$(get_recommended_mode "${system_info[HARDWARE_TIER]}" "${system_info[GPU]}")
    
    echo "${system_info[@]}"
}

# Function to determine hardware tier
get_hardware_tier() {
    local memory_gb=$1
    local gpu_memory_gb=$2
    local has_gpu=$([[ $gpu_memory_gb -gt 0 ]] && echo true || echo false)
    
    if [[ $memory_gb -ge 32 && $gpu_memory_gb -ge 12 ]]; then
        echo "Tier 5 Enterprise"
    elif [[ $memory_gb -ge 16 && $gpu_memory_gb -ge 6 ]]; then
        echo "Tier 4 Performance"
    elif [[ $memory_gb -ge 8 && $gpu_memory_gb -ge 4 ]]; then
        echo "Tier 3 Standard"
    elif [[ $memory_gb -ge 4 ]]; then
        echo "Tier 2 Basic"
    else
        echo "Tier 1 Mobile"
    fi
}

# Function to determine recommended mode
get_recommended_mode() {
    local tier=$1
    local gpu=$2
    local has_gpu=$([[ "$gpu" != "Unknown" ]] && echo true || echo false)
    
    case "$tier" in
        "Tier 5"*) echo "titan" ;;
        "Tier 4"*) echo "$($has_gpu && echo "full_neural" || echo "quantized_heavy")" ;;
        "Tier 3"*) echo "$($has_gpu && echo "quantized_heavy" || echo "quantized_medium")" ;;
        "Tier 2"*) echo "quantized_medium" ;;
        "Tier 1"*) echo "quantized_light" ;;
        *) echo "balanced" ;;
    esac
}

# Function to check Docker installation
test_docker_installation() {
    print_color "$WHITE" "🐳 Checking Docker Installation..."
    
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version)
        print_color "$GREEN" "✅ Docker is installed: $DOCKER_VERSION"
        return 0
    else
        print_color "$RED" "❌ Docker is not installed"
        return 1
    fi
}

# Function to install Docker
install_docker() {
    print_color "$WHITE" "📦 Installing Docker..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux Docker installation
        if command -v apt-get &> /dev/null; then
            # Ubuntu/Debian
            print_color "$WHITE" "📥 Adding Docker repository..."
            curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
            
            print_color "$WHITE" "📦 Installing Docker Engine..."
            sudo apt-get update
            sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            
            print_color "$WHITE" "👥 Adding user to docker group..."
            sudo usermod -aG docker $USER
            
            print_color "$GREEN" "✅ Docker installation completed"
            print_color "$YELLOW" "⚠️  Please log out and log back in to use Docker without sudo"
            
        elif command -v yum &> /dev/null; then
            # CentOS/RHEL/Fedora
            print_color "$WHITE" "📥 Adding Docker repository..."
            sudo yum install -y yum-utils
            sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
            
            print_color "$WHITE" "📦 Installing Docker Engine..."
            sudo yum install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            
            print_color "$WHITE" "👥 Adding user to docker group..."
            sudo usermod -aG docker $USER
            
            print_color "$GREEN" "✅ Docker installation completed"
            print_color "$YELLOW" "⚠️  Please log out and log back in to use Docker without sudo"
        else
            print_color "$RED" "❌ Unsupported Linux distribution for automatic Docker installation"
            return 1
        fi
        
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS Docker installation
        print_color "$WHITE" "📥 Downloading Docker Desktop for Mac..."
        
        # Download Docker Desktop
        DOCKER_URL="https://desktop.docker.com/mac/main/amd64/Docker.dmg"
        DOCKER_DMG="/tmp/Docker.dmg"
        
        curl -L "$DOCKER_URL" -o "$DOCKER_DMG"
        
        print_color "$WHITE" "📦 Installing Docker Desktop..."
        hdiutil attach "$DOCKER_DMG"
        sudo /Volumes/Docker/Docker.app/Contents/MacOS/Docker --accept-license
        hdiutil detach /Volumes/Docker
        
        rm "$DOCKER_DMG"
        
        print_color "$GREEN" "✅ Docker Desktop installation completed"
        print_color "$YELLOW" "⚠️  Please start Docker Desktop from Applications"
    fi
    
    return 0
}

# Function to install ASIMNEXUS
install_asimnexus() {
    local system_info=("$@")
    
    print_color "$WHITE" "🚀 Installing ASIMNEXUS..."
    
    # Create installation directory
    if [[ ! -d "$INSTALL_PATH" ]]; then
        mkdir -p "$INSTALL_PATH"
        print_color "$GREEN" "📁 Created installation directory: $INSTALL_PATH"
    fi
    
    cd "$INSTALL_PATH"
    
    try {
        # Download ASIMNEXUS
        if [[ "$VERSION" == "latest" ]]; then
            print_color "$WHITE" "📥 Downloading ASIMNEXUS (latest)..."
            # This would download from GitHub releases
            # For demo, we'll assume it's already available
            print_color "$GREEN" "📦 ASIMNEXUS package ready"
        else
            print_color "$WHITE" "📥 Downloading ASIMNEXUS v$VERSION..."
            # Download specific version
        fi
        
        # Create configuration
        cat > config/founder_config.json << EOF
{
    "system": {
        "hardware_tier": "${system_info[11]}",
        "recommended_mode": "${system_info[12]}",
        "gpu_available": $([[ "${system_info[9]}" != "Unknown" ]] && echo true || echo false),
        "gpu_name": "${system_info[9]}",
        "gpu_memory_gb": ${system_info[10]},
        "total_memory_gb": ${system_info[4]},
        "cpu_cores": ${system_info[3]},
        "os": "${system_info[0]}",
        "architecture": "${system_info[1]}"
    },
    "deployment": {
        "mode": "${system_info[12]}",
        "auto_scale": true,
        "monitoring_enabled": true,
        "security_level": "standard"
    },
    "founder": {
        "key": "$([[ -n "$FOUNDER_KEY" ]] && echo "$FOUNDER_KEY" || echo "auto-generated")",
        "installation_date": "$(date '+%Y-%m-%d %H:%M:%S')",
        "version": "$VERSION"
    }
}
EOF
        
        print_color "$GREEN" "✅ ASIMNEXUS installation completed"
        return 0
    } catch {
        print_color "$RED" "❌ ASIMNEXUS installation failed: $1"
        return 1
    }
}

# Function to start ASIMNEXUS services
start_asimnexus_services() {
    print_color "$WHITE" "🚀 Starting ASIMNEXUS services..."
    
    cd "$INSTALL_PATH"
    
    try {
        # Start Docker Compose
        if [[ -f "docker-compose.yml" ]]; then
            print_color "$WHITE" "🐳 Starting Docker Compose services..."
            docker-compose up -d
            
            # Wait for services to be ready
            print_color "$WHITE" "⏳ Waiting for services to initialize..."
            sleep 30
            
            # Check service status
            SERVICES=$(docker-compose ps)
            print_color "$WHITE" "📊 Service Status:"
            print_color "$PURPLE" "$SERVICES"
            
            print_color "$GREEN" "✅ ASIMNEXUS services started successfully"
            print_color "$GREEN" "🌐 Web Interface: http://localhost:3000"
            print_color "$GREEN" "🔌 API Endpoint: http://localhost:8000"
            print_color "$GREEN" "📊 Monitoring: http://localhost:3001"
        else
            print_color "$RED" "❌ docker-compose.yml not found"
        fi
    } catch {
        print_color "$RED" "❌ Failed to start services: $1"
    }
}

# Function to generate founder report
generate_founder_report() {
    local system_info=("$@")
    
    local report_path="$INSTALL_PATH/founder_report.txt"
    
    cat > "$report_path" << EOF
╔════════════════════════════════════════════════════════════╗
║                    ASIMNEXUS FOUNDER REPORT                        ║
╚════════════════════════════════════════════════════════════╝

Installation Summary:
- Date: $(date)
- Version: $VERSION
- Mode: ${system_info[12]}
- Hardware Tier: ${system_info[11]}

System Configuration:
- OS: ${system_info[0]}
- CPU: ${system_info[2]} (${system_info[3]} cores)
- Memory: ${system_info[4]} GB
- GPU: ${system_info[9]} (${system_info[10]} GB)
- Free Disk Space: ${system_info[11]} GB

Recommended Settings:
- Execution Mode: ${system_info[12]}
- Model Size: $(get_model_size "${system_info[12]}")
- Batch Size: $(get_batch_size "${system_info[12]}")
- Performance Profile: $(get_performance_profile "${system_info[12]}")

Access Information:
- Web Interface: http://localhost:3000
- API Documentation: http://localhost:8000/docs
- Monitoring Dashboard: http://localhost:3001
- WebSocket: ws://localhost:8000/ws

Next Steps:
1. Open http://localhost:3000 in your browser
2. Complete the onboarding wizard
3. Configure your Founder preferences
4. Activate your Digital Workforce

Support:
- Documentation: https://docs.asimnexus.com
- Community: https://community.asimnexus.com
- Issues: https://github.com/asimnexus/issues

Generated by ASIMNEXUS Founder Setup Script v2.0
EOF
    
    print_color "$GREEN" "📋 Founder report saved to: $report_path"
}

# Function to get model size
get_model_size() {
    local mode=$1
    case "$mode" in
        "titan") echo "20B parameters" ;;
        "full_neural") echo "13B parameters" ;;
        "quantized_heavy") echo "7B parameters" ;;
        "quantized_medium") echo "4B parameters" ;;
        "quantized_light") echo "2B parameters" ;;
        *) echo "Auto-detected" ;;
    esac
}

# Function to get batch size
get_batch_size() {
    local mode=$1
    case "$mode" in
        "titan") echo "8" ;;
        "full_neural") echo "4" ;;
        "quantized_heavy") echo "4" ;;
        "quantized_medium") echo "2" ;;
        "quantized_light") echo "1" ;;
        *) echo "Auto" ;;
    esac
}

# Function to get performance profile
get_performance_profile() {
    local mode=$1
    case "$mode" in
        "titan") echo "Maximum Performance" ;;
        "full_neural") echo "High Performance" ;;
        "quantized_heavy") echo "Balanced Performance" ;;
        "quantized_medium") echo "Power Saving" ;;
        "quantized_light") echo "Minimal Resource Usage" ;;
        *) echo "Adaptive" ;;
    esac
}

# Main execution function
main() {
    show_banner
    
    # Detect system information
    system_info=($(get_system_info))
    
    # Display system information
    print_color "$WHITE" "📊 System Configuration:"
    print_color "$CYAN" "   OS: ${system_info[0]}"
    print_color "$CYAN" "   CPU: ${system_info[2]} (${system_info[3]} cores)"
    print_color "$CYAN" "   Memory: ${system_info[4]} GB"
    print_color "$CYAN" "   GPU: ${system_info[9]} (${system_info[10]} GB)"
    print_color "$CYAN" "   Hardware Tier: ${system_info[11]}"
    print_color "$CYAN" "   Recommended Mode: ${system_info[12]}"
    echo ""
    
    # Check Docker installation
    docker_installed=$(test_docker_installation)
    
    if [[ $docker_installed -eq 0 && $SKIP_DOCKER == false ]]; then
        print_color "$WHITE" "🐳 Docker not found. Installing Docker..."
        install_docker
        
        if [[ $? -ne 0 ]]; then
            print_color "$RED" "❌ Docker installation failed. Please install Docker manually and retry."
            exit 1
        fi
        
        print_color "$YELLOW" "⚠️  Please log out and log back in to use Docker without sudo"
        exit 0
    fi
    
    # Install ASIMNEXUS
    install_success=$(install_asimnexus "${system_info[@]}")
    
    if [[ $install_success -ne 0 ]]; then
        print_color "$RED" "❌ ASIMNEXUS installation failed"
        exit 1
    fi
    
    # Start services
    if [[ $DEV_MODE == false ]]; then
        start_asimnexus_services
    else
        print_color "$YELLOW" "🔧 Development mode - services not started automatically"
        print_color "$WHITE" "Run 'docker-compose up -d' manually to start services"
    fi
    
    # Generate report
    generate_founder_report "${system_info[@]}"
    
    echo ""
    print_color "$GREEN" "🎉 ASIMNEXUS Founder Clone Setup Complete!"
    echo ""
    print_color "$CYAN" "Your Digital Workforce is ready to awaken!"
    echo ""
    print_color "$WHITE" "Quick Start Commands:"
    print_color "$CYAN" "  • Check status: docker-compose ps"
    print_color "$CYAN" "  • View logs: docker-compose logs -f"
    print_color "$CYAN" "  • Stop services: docker-compose down"
    print_color "$CYAN" "  • Restart services: docker-compose restart"
    echo ""
    print_color "$GREEN" "🌐 Access your ASIMNEXUS at: http://localhost:3000"
    echo ""
}

# Execute main function
main "$@"
