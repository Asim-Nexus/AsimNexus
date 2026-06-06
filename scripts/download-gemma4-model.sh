#!/bin/bash

# ASIMNEXUS Gemma 4 Model Download Script
# ========================================
# Downloads Gemma 4 quantized model for local use

set -e

# Configuration
MODEL_NAME="gemma-4-7b-it"
MODEL_VERSION="Q4_K_M"
MODEL_DIR="./models"
MODEL_FILE="${MODEL_NAME}.${MODEL_VERSION}.gguf"
MODEL_URL="https://huggingface.co/google/${MODEL_NAME}-gguf/resolve/main/${MODEL_FILE}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}ASIMNEXUS Gemma 4 Model Download${NC}"
echo "==================================="
echo ""

# Create models directory
echo -e "${YELLOW}Creating models directory...${NC}"
mkdir -p ${MODEL_DIR}
echo -e "${GREEN}✓ Models directory created${NC}"
echo ""

# Check if model already exists
if [ -f "${MODEL_DIR}/${MODEL_FILE}" ]; then
    echo -e "${YELLOW}Model already exists: ${MODEL_DIR}/${MODEL_FILE}${NC}"
    echo "Skipping download."
    exit 0
fi

# Download model
echo -e "${YELLOW}Downloading Gemma 4 7B ${MODEL_VERSION}...${NC}"
echo "This may take a while (model size: ~4.5GB)"
echo ""

# Try wget first
if command -v wget &> /dev/null; then
    wget -O "${MODEL_DIR}/${MODEL_FILE}" "${MODEL_URL}"
# Try curl if wget not available
elif command -v curl &> /dev/null; then
    curl -L -o "${MODEL_DIR}/${MODEL_FILE}" "${MODEL_URL}"
else
    echo "Neither wget nor curl found. Please install one of them."
    exit 1
fi

echo ""
echo -e "${GREEN}✓ Model downloaded successfully${NC}"
echo ""
echo "Model Details:"
echo "  File: ${MODEL_DIR}/${MODEL_FILE}"
echo "  Size: $(du -h ${MODEL_DIR}/${MODEL_FILE} | cut -f1)"
echo "  Type: GGUF (Quantized)"
echo "  Quantization: ${MODEL_VERSION}"
echo ""
echo "Next Steps:"
echo "  1. Run ASIMNEXUS: python main.py"
echo "  2. Or use Docker: docker-compose up"
