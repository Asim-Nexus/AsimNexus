#!/bin/bash

# ASIMNEXUS Oracle Always Free Setup Script
# ==========================================
# Deploys ASIMNEXUS on Oracle Cloud Always Free Tier
# - 2 OCPU, 24GB RAM (Always Free)
# - 200GB Block Volume Storage (Always Free)
# - 10TB Egress/Month (Always Free)

set -e

# Configuration
COMPARTMENT_ID="${OCI_COMPARTMENT_ID:-your-compartment-ocid}"
REGION="us-ashburn-1"
INSTANCE_NAME="asimnexus-always-free"
SHAPE="AMD.Standard.E4.Flex"
OCPU="2"
MEMORY="24"
SSH_KEY_PATH="${HOME}/.ssh/id_rsa.pub"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}ASIMNEXUS Oracle Always Free Setup${NC}"
echo "======================================"
echo ""

# Check oci CLI
echo -e "${YELLOW}Checking oci CLI...${NC}"
if ! command -v oci &> /dev/null; then
    echo -e "${RED}oci CLI not found. Please install it first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ oci CLI found${NC}"

# Check oci authentication
echo -e "${YELLOW}Checking oci authentication...${NC}"
if ! oci iam user get > /dev/null 2>&1; then
    echo -e "${RED}oci CLI not authenticated. Please run 'oci setup config'${NC}"
    exit 1
fi
echo -e "${GREEN}✓ oci authenticated${NC}"

# Get compartment ID if not provided
if [ "${COMPARTMENT_ID}" == "your-compartment-ocid" ]; then
    echo -e "${YELLOW}Getting compartment ID...${NC}"
    COMPARTMENT_ID=$(oci iam compartment list --compartment-id-in-subtree true --query "data[?name=='root'] | [0].id" --raw-output)
    echo -e "${GREEN}✓ Compartment ID: ${COMPARTMENT_ID}${NC}"
fi

# Check SSH key
echo -e "${YELLOW}Checking SSH key...${NC}"
if [ ! -f "${SSH_KEY_PATH}" ]; then
    echo -e "${YELLOW}SSH key not found at ${SSH_KEY_PATH}. Generating...${NC}"
    ssh-keygen -t rsa -b 2048 -f "${SSH_KEY_PATH%.*}" -N ""
fi
SSH_KEY=$(cat ${SSH_KEY_PATH})
echo -e "${GREEN}✓ SSH key found${NC}"

# Get subnet ID
echo -e "${YELLOW}Getting subnet ID...${NC}"
SUBNET_ID=$(oci network subnet list \
    --compartment-id ${COMPARTMENT_ID} \
    --query "data[0].id" \
    --raw-output)

if [ -z "${SUBNET_ID}" ]; then
    echo -e "${RED}No subnet found. Please create a VCN and subnet first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Subnet ID: ${SUBNET_ID}${NC}"

# Get image ID (Oracle Linux)
echo -e "${YELLOW}Getting image ID...${NC}"
IMAGE_ID=$(oci compute image list \
    --compartment-id ${COMPARTMENT_ID} \
    --operating-system "Oracle Linux" \
    --shape ${SHAPE} \
    --query "data[0].id" \
    --raw-output)
echo -e "${GREEN}✓ Image ID: ${IMAGE_ID}${NC}"

# Launch instance
echo -e "${YELLOW}Launching instance (${SHAPE})...${NC}"
INSTANCE_ID=$(oci compute instance launch \
    --compartment-id ${COMPARTMENT_ID} \
    --availability-domain "UxkI:US-ASHBURN-AD-1" \
    --shape ${SHAPE} \
    --shape-config '{"ocpus": '${OCPU}', "memoryInGBs": '${MEMORY}'}' \
    --source-details '{"sourceType": "image", "sourceId": "'${IMAGE_ID}'"}' \
    --create-vnic-details '{"subnetId": "'${SUBNET_ID}'", "assignPublicIp": true}' \
    --ssh-key-ids "${SSH_KEY}" \
    --display-name ${INSTANCE_NAME} \
    --wait-for-state RUNNING \
    --query "data.id" \
    --raw-output)

echo -e "${GREEN}✓ Instance launched: ${INSTANCE_ID}${NC}"

# Get public IP
echo -e "${YELLOW}Getting public IP...${NC}"
PUBLIC_IP=$(oci compute instance list-vnics \
    --instance-id ${INSTANCE_ID} \
    --query "data[0].publicIp" \
    --raw-output)

echo -e "${GREEN}✓ Public IP: ${PUBLIC_IP}${NC}"

echo ""
echo -e "${GREEN}======================================${NC}"
echo -e "${GREEN}✓ Oracle Always Free Setup Complete${NC}"
echo -e "${GREEN}======================================${NC}"
echo ""
echo "Instance Details:"
echo "  Instance ID: ${INSTANCE_ID}"
echo "  Instance Name: ${INSTANCE_NAME}"
echo "  Shape: ${SHAPE}"
echo "  OCPUs: ${OCPU}"
echo "  Memory: ${MEMORY}GB"
echo "  Public IP: ${PUBLIC_IP}"
echo "  Region: ${REGION}"
echo "  SSH Command: ssh -i ${SSH_KEY_PATH%.*} opc@${PUBLIC_IP}"
echo ""
echo "Always Free Tier Info:"
echo "  - 2 OCPU, 24GB RAM (Forever Free)"
echo "  - 200GB Block Volume Storage (Forever Free)"
echo "  - 10TB Egress/Month (Forever Free)"
echo "  - 4 Arm Ampere A1 cores, 24GB RAM (Forever Free)"
echo "  - Cost: $0/month (Forever)"
echo ""
echo "Next Steps:"
echo "  1. SSH into instance: ssh -i ${SSH_KEY_PATH%.*} opc@${PUBLIC_IP}"
echo "  2. Install Docker: curl -fsSL https://get.docker.com | sh"
echo "  3. Clone ASIMNEXUS repository"
echo "  4. Run docker-compose up -d"
echo "  5. Access at http://${PUBLIC_IP}:8000"
echo ""
echo "To stop instance:"
echo "  oci compute instance action --action STOP --instance-id ${INSTANCE_ID}"
echo ""
echo "To terminate instance:"
echo "  oci compute instance terminate --instance-id ${INSTANCE_ID}"
