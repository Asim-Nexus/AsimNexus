#!/bin/bash

# ASIMNEXUS Azure Container Instances Free Tier Setup Script
# ============================================================
# Deploys ASIMNEXUS on Azure Container Instances (750 hours free/month)
# Optimized for maximum free tier usage

set -e

# Configuration
RESOURCE_GROUP="asimnexus-rg-free-tier"
CONTAINER_NAME="asimnexus"
LOCATION="eastus"
CPU="1"
MEMORY="1.0"
PORT="8000"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}ASIMNEXUS Azure Container Instances Free Tier Setup${NC}"
echo "=========================================================="
echo ""

# Check az CLI
echo -e "${YELLOW}Checking az CLI...${NC}"
if ! command -v az &> /dev/null; then
    echo -e "${RED}az CLI not found. Please install it first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ az CLI found${NC}"

# Check az authentication
echo -e "${YELLOW}Checking az authentication...${NC}"
if ! az account show > /dev/null 2>&1; then
    echo -e "${YELLOW}Not authenticated. Running az login...${NC}"
    az login
fi
echo -e "${GREEN}✓ az authenticated${NC}"

# Get subscription ID
SUBSCRIPTION_ID=$(az account show --query id -o tsv)
echo -e "${GREEN}Subscription ID: ${SUBSCRIPTION_ID}${NC}"
echo ""

# Create resource group
echo -e "${YELLOW}Creating resource group...${NC}"
if az group show --name ${RESOURCE_GROUP} > /dev/null 2>&1; then
    echo -e "${YELLOW}Resource group already exists${NC}"
else
    az group create \
        --name ${RESOURCE_GROUP} \
        --location ${LOCATION}
    echo -e "${GREEN}✓ Resource group created${NC}"
fi

# Create container registry (if needed)
REGISTRY_NAME="${RESOURCE_GROUP}acr"
echo -e "${YELLOW}Creating container registry...${NC}"
if az acr show --name ${REGISTRY_NAME} --resource-group ${RESOURCE_GROUP} > /dev/null 2>&1; then
    echo -e "${YELLOW}Container registry already exists${NC}"
else
    az acr create \
        --resource-group ${RESOURCE_GROUP} \
        --name ${REGISTRY_NAME} \
        --sku Basic \
        --location ${LOCATION}
    echo -e "${GREEN}✓ Container registry created${NC}"
fi

# Get registry login server
REGISTRY_SERVER=$(az acr show --name ${REGISTRY_NAME} --resource-group ${RESOURCE_GROUP} --query loginServer -o tsv)

# Login to registry
echo -e "${YELLOW}Logging into container registry...${NC}"
az acr login --name ${REGISTRY_NAME}

# Build and push Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
docker build -t ${REGISTRY_SERVER}/${CONTAINER_NAME}:latest .

echo -e "${YELLOW}Pushing Docker image...${NC}"
docker push ${REGISTRY_SERVER}/${CONTAINER_NAME}:latest

# Create container instance
echo -e "${YELLOW}Creating container instance...${NC}"
CONTAINER_IP=$(az container create \
    --resource-group ${RESOURCE_GROUP} \
    --name ${CONTAINER_NAME} \
    --image ${REGISTRY_SERVER}/${CONTAINER_NAME}:latest \
    --cpu ${CPU} \
    --memory ${MEMORY} \
    --ports ${PORT} \
    --location ${LOCATION} \
    --query ipAddress.ip \
    -o tsv)

echo -e "${GREEN}✓ Container instance created${NC}"

echo ""
echo -e "${GREEN}==========================================================${NC}"
echo -e "${GREEN}✓ Azure Container Instances Free Tier Setup Complete${NC}"
echo -e "${GREEN}==========================================================${NC}"
echo ""
echo "Container Details:"
echo "  Container Name: ${CONTAINER_NAME}"
echo "  Resource Group: ${RESOURCE_GROUP}"
echo "  Location: ${LOCATION}"
echo "  Public IP: ${CONTAINER_IP}"
echo "  Port: ${PORT}"
echo "  CPU: ${CPU}"
echo "  Memory: ${MEMORY}GB"
echo ""
echo "Free Tier Info:"
echo "  - 750 hours/month free"
echo "  - 1 vCPU, 1GB RAM"
echo "  - Cost after free tier: ~$7.50/month"
echo ""
echo "Next Steps:"
echo "  1. Test deployment: curl http://${CONTAINER_IP}:${PORT}"
echo "  2. View logs: az container logs --resource-group ${RESOURCE_GROUP} --name ${CONTAINER_NAME}"
echo "  3. Monitor usage: az container show --resource-group ${RESOURCE_GROUP} --name ${CONTAINER_NAME}"
echo ""
echo "To stop container (save free tier hours):"
echo "  az container stop --resource-group ${RESOURCE_GROUP} --name ${CONTAINER_NAME}"
echo ""
echo "To delete container:"
echo "  az container delete --resource-group ${RESOURCE_GROUP} --name ${CONTAINER_NAME}"
