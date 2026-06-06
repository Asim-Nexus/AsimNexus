#!/bin/bash
# ASIMNEXUS Universal Installer
# ==============================
# One-line install: curl -fsSL install.asimnexus.org | bash
#
# Supports: Linux, macOS, Windows (WSL/Git Bash)
# Architectures: x64, arm64, armv7

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/asimnexus/asimnexus"
INSTALL_DIR="${HOME}/.asimnexus"
VERSION="2.0.0"

# Detect OS and architecture
detect_platform() {
    OS="$(uname -s)"
    ARCH="$(uname -m)"
    
    case "$OS" in
        Linux*)     PLATFORM='linux';;
        Darwin*)    PLATFORM='macos';;
        CYGWIN*|MINGW*|MSYS*) PLATFORM='windows';;
        *)          PLATFORM='unknown';;
    esac
    
    case "$ARCH" in
        x86_64)     ARCH='amd64';;
        amd64)      ARCH='amd64';;
        arm64)      ARCH='arm64';;
        aarch64)    ARCH='arm64';;
        armv7l)     ARCH='armv7';;
        *)          ARCH='unknown';;
    esac
    
    echo -e "${BLUE}Detected: $PLATFORM / $ARCH${NC}"
}

# Print banner
print_banner() {
    echo -e "${BLUE}"
    echo "    █████╗ ███████╗██╗███╗   ███╗███╗   ██╗███████╗██╗  ██╗██╗   ██╗███████╗"
    echo "   ██╔══██╗██╔════╝██║████╗ ████║████╗  ██║██╔════╝╚██╗██╔╝██║   ██║██╔════╝"
    echo "   ███████║███████╗██║██╔████╔██║██╔██╗ ██║█████╗   ╚███╔╝ ██║   ██║███████╗"
    echo "   ██╔══██║╚════██║██║██║╚██╔╝██║██║╚██╗██║██╔══╝   ██╔██╗ ██║   ██║╚════██║"
    echo "   ██║  ██║███████║██║██║ ╚═╝ ██║██║ ╚████║███████╗██╔╝ ██╗╚██████╔╝███████║"
    echo "   ╚═╝  ╚═╝╚══════╝╚═╝╚═╝     ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝"
    echo -e "${NC}"
    echo -e "${GREEN}   World Operating System — Version $VERSION${NC}"
    echo -e "${YELLOW}   Civilization Architecture for 8 Billion People${NC}"
    echo ""
}

# Check dependencies
check_deps() {
    echo -e "${BLUE}Checking dependencies...${NC}"
    
    MISSING_DEPS=()
    
    if ! command -v python3 &> /dev/null; then
        MISSING_DEPS+=("python3")
    fi
    
    if ! command -v pip3 &> /dev/null; then
        MISSING_DEPS+=("pip3")
    fi
    
    if ! command -v git &> /dev/null; then
        MISSING_DEPS+=("git")
    fi
    
    if [ ${#MISSING_DEPS[@]} -ne 0 ]; then
        echo -e "${RED}Missing dependencies: ${MISSING_DEPS[*]}${NC}"
        echo -e "${YELLOW}Please install them first:${NC}"
        
        case "$PLATFORM" in
            linux)
                echo "  Ubuntu/Debian: sudo apt-get update && sudo apt-get install -y python3 python3-pip git"
                echo "  Fedora: sudo dnf install -y python3 python3-pip git"
                echo "  Arch: sudo pacman -S python python-pip git"
                ;;
            macos)
                echo "  brew install python3 git"
                ;;
            windows)
                echo "  Download from: https://python.org and https://git-scm.com"
                ;;
        esac
        exit 1
    fi
    
    echo -e "${GREEN}✓ All dependencies present${NC}"
}

# Install AsimNexus
install_asimnexus() {
    echo -e "${BLUE}Installing AsimNexus...${NC}"
    
    # Create install directory
    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"
    
    # Clone or update repository
    if [ -d "asimnexus" ]; then
        echo -e "${YELLOW}Existing installation found, updating...${NC}"
        cd asimnexus
        git pull origin main
    else
        echo -e "${BLUE}Cloning repository...${NC}"
        git clone --depth 1 "$REPO_URL" asimnexus
        cd asimnexus
    fi
    
    # Create virtual environment
    echo -e "${BLUE}Creating Python virtual environment...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    
    # Install dependencies
    echo -e "${BLUE}Installing Python dependencies...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Install optional dependencies based on platform
    case "$PLATFORM" in
        linux)
            # Check for GPU (CUDA)
            if command -v nvidia-smi &> /dev/null; then
                echo -e "${GREEN}NVIDIA GPU detected, installing CUDA support...${NC}"
                pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
            fi
            ;;
        macos)
            echo -e "${GREEN}macOS detected, installing Metal support...${NC}"
            pip install torch torchvision torchaudio
            ;;
    esac
    
    # Create data directories
    mkdir -p data/users data/models memory logs config
    
    # Setup environment
    if [ ! -f ".env" ]; then
        cp .env.example .env
        echo -e "${YELLOW}Created .env file. Please edit it with your settings.${NC}"
    fi
    
    echo -e "${GREEN}✓ Installation complete!${NC}"
}

# Create launcher script
create_launcher() {
    echo -e "${BLUE}Creating launcher...${NC}"
    
    LAUNCHER_PATH="$INSTALL_DIR/asimnexus"
    
    cat > "$LAUNCHER_PATH" << 'EOF'
#!/bin/bash
# AsimNexus Launcher

ASIM_DIR="${HOME}/.asimnexus/asimnexus"
cd "$ASIM_DIR"

# Activate virtual environment
source venv/bin/activate

# Parse arguments
MODE="${1:-normal}"

 case "$MODE" in
    offline|--offline)
        echo "Starting AsimNexus in OFFLINE mode..."
        python main.py --offline
        ;;
    dev|--dev)
        echo "Starting AsimNexus in DEVELOPMENT mode..."
        python main.py --dev
        ;;
    backend|--backend)
        echo "Starting AsimNexus BACKEND only..."
        python main.py --no-frontend
        ;;
    *)
        echo "Starting AsimNexus..."
        python main.py
        ;;
esac
EOF
    
    chmod +x "$LAUNCHER_PATH"
    
    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
        echo "export PATH=\"\$PATH:$INSTALL_DIR\"" >> ~/.bashrc
        echo -e "${YELLOW}Added to PATH. Run: source ~/.bashrc${NC}"
    fi
    
    echo -e "${GREEN}✓ Launcher created at: $LAUNCHER_PATH${NC}"
}

# Print usage
print_usage() {
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  AsimNexus Installation Complete!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BLUE}Usage:${NC}"
    echo "  asimnexus              # Start normally"
    echo "  asimnexus offline      # Offline mode (local LLM only)"
    echo "  asimnexus dev          # Development mode (hot reload)"
    echo "  asimnexus backend      # Backend only (no frontend)"
    echo ""
    echo -e "${BLUE}Or manually:${NC}"
    echo "  cd $INSTALL_DIR/asimnexus"
    echo "  source venv/bin/activate"
    echo "  python main.py"
    echo ""
    echo -e "${BLUE}Access:${NC}"
    echo "  Frontend: http://localhost:3000"
    echo "  API:      http://localhost:8000"
    echo "  Docs:     http://localhost:8000/docs"
    echo "  Health:   http://localhost:8000/health"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Edit .env file: nano $INSTALL_DIR/asimnexus/.env"
    echo "  2. Start AsimNexus: asimnexus"
    echo "  3. Register account at: http://localhost:3000"
    echo ""
}

# Main
main() {
    print_banner
    detect_platform
    check_deps
    install_asimnexus
    create_launcher
    print_usage
    
    echo -e "${GREEN}🌟 Welcome to AsimNexus — One Kernel, Infinite Worlds${NC}"
}

main "$@"
