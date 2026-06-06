#!/bin/bash

# ASIMNEXUS GCP Cloud Run Free Tier Setup Script
# ===============================================
# Deploys ASIMNEXUS on GCP Cloud Run (2M requests free/month)
# Optimized for maximum free tier usage

set -e

# Configuration
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-your-project-id}"
REGION="us-central1"
SERVICE_NAME="asimnexus"
MEMORY="512Mi"
CPU="1"
MAX_INSTANCES="10"
MIN_INSTANCES="0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}ASIMNEXUS GCP Cloud Run Free Tier Setup${NC}"
echo "=============================================="
echo ""

# Check gcloud CLI
echo -e "${YELLOW}Checking gcloud CLI...${NC}"
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}gcloud CLI not found. Please install it first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ gcloud CLI found${NC}"

# Check gcloud authentication
echo -e "${YELLOW}Checking gcloud authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo -e "${YELLOW}Not authenticated. Running gcloud auth login...${NC}"
    gcloud auth login
fi
echo -e "${GREEN}✓ gcloud authenticated${NC}"

# Set project
echo -e "${YELLOW}Setting project: ${PROJECT_ID}${NC}"
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo -e "${YELLOW}Enabling required APIs...${NC}"
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    --project=${PROJECT_ID}
echo -e "${GREEN}✓ APIs enabled${NC}"

# Build Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
gcloud builds submit \
    --tag gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest \
    --project=${PROJECT_ID} \
    --timeout=600
echo -e "${GREEN}✓ Docker image built${NC}"

# Deploy to Cloud Run
echo -e "${YELLOW}Deploying to Cloud Run...${NC}"
SERVICE_URL=$(gcloud run deploy ${SERVICE_NAME} \
    --image gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest \
    --platform managed \
    --region ${REGION} \
    --memory ${MEMORY} \
    --cpu ${CPU} \
    --max-instances ${MAX_INSTANCES} \
    --min-instances ${MIN_INSTANCES} \
    --allow-unauthenticated \
    --project=${PROJECT_ID} \
    --format="value(status.url)")

echo -e "${GREEN}✓ Cloud Run service deployed${NC}"

echo ""
echo -e "${GREEN}==============================================${NC}"
echo -e "${GREEN}✓ GCP Cloud Run Free Tier Setup Complete${NC}"
echo -e "${GREEN}==============================================${NC}"
echo ""
echo "Service Details:"
echo "  Service Name: ${SERVICE_NAME}"
echo "  Region: ${REGION}"
echo "  Service URL: ${SERVICE_URL}"
echo "  Memory: ${MEMORY}"
echo "  CPU: ${CPU}"
echo "  Max Instances: ${MAX_INSTANCES}"
echo "  Min Instances: ${MIN_INSTANCES}"
echo ""
echo "Free Tier Info:"
echo "  - 2 million requests/month free"
echo "  - 180,000 vCPU-seconds free"
echo "  - 360,000 GB-seconds memory free"
echo "  - 2 GB egress/month free"
echo "  - Cost after free tier: ~$0.40/1M requests"
echo ""
echo "Next Steps:"
echo "  1. Test deployment: curl ${SERVICE_URL}"
echo "  2. View logs: gcloud logs tail ${SERVICE_NAME} --region ${REGION}"
echo "  3. Monitor usage: gcloud run services describe ${SERVICE_NAME} --region ${REGION}"
echo ""
echo "To stop service (save free tier):"
echo "  gcloud run services delete ${SERVICE_NAME} --region ${REGION}"
