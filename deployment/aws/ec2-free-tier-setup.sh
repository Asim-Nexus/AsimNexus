#!/bin/bash

# ASIMNEXUS AWS EC2 Free Tier Setup Script
# =========================================
# Deploys ASIMNEXUS on AWS EC2 t2.micro (750 hours free/month)
# Optimized for maximum free tier usage

set -e

# Configuration
INSTANCE_TYPE="t2.micro"
AMI_ID="ami-0c55b159cbfafe1f0"  # Ubuntu 22.04 LTS (us-east-1)
KEY_NAME="asimnexus-key"
SECURITY_GROUP="asimnexus-sg-free-tier"
REGION="us-east-1"
PROJECT_NAME="asimnexus"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}ASIMNEXUS AWS EC2 Free Tier Setup${NC}"
echo "=========================================="
echo ""

# Check AWS CLI
echo -e "${YELLOW}Checking AWS CLI...${NC}"
if ! command -v aws &> /dev/null; then
    echo -e "${RED}AWS CLI not found. Please install it first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ AWS CLI found${NC}"

# Check AWS credentials
echo -e "${YELLOW}Checking AWS credentials...${NC}"
aws sts get-caller-identity > /dev/null 2>&1 || {
    echo -e "${RED}AWS credentials not configured. Run 'aws configure' first.${NC}"
    exit 1
}
echo -e "${GREEN}✓ AWS credentials configured${NC}"

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}AWS Account ID: ${AWS_ACCOUNT_ID}${NC}"
echo ""

# Create key pair
echo -e "${YELLOW}Creating key pair...${NC}"
if aws ec2 describe-key-pairs --key-names ${KEY_NAME} --region ${REGION} > /dev/null 2>&1; then
    echo -e "${YELLOW}Key pair already exists${NC}"
else
    aws ec2 create-key-pair \
        --key-name ${KEY_NAME} \
        --region ${REGION} \
        --query 'KeyMaterial' \
        --output text > ${KEY_NAME}.pem
    chmod 400 ${KEY_NAME}.pem
    echo -e "${GREEN}✓ Key pair created: ${KEY_NAME}.pem${NC}"
fi

# Create security group
echo -e "${YELLOW}Creating security group...${NC}"
if aws ec2 describe-security-groups --group-names ${SECURITY_GROUP} --region ${REGION} > /dev/null 2>&1; then
    echo -e "${YELLOW}Security group already exists${NC}"
    SG_ID=$(aws ec2 describe-security-groups --group-names ${SECURITY_GROUP} --region ${REGION} --query 'SecurityGroups[0].GroupId' --output text)
else
    SG_ID=$(aws ec2 create-security-group \
        --group-name ${SECURITY_GROUP} \
        --description "ASIMNEXUS Free Tier Security Group" \
        --region ${REGION} \
        --query 'GroupId' \
        --output text)
    
    # Allow SSH
    aws ec2 authorize-security-group-ingress \
        --group-id ${SG_ID} \
        --protocol tcp \
        --port 22 \
        --cidr 0.0.0.0/0 \
        --region ${REGION} > /dev/null 2>&1 || true
    
    # Allow HTTP
    aws ec2 authorize-security-group-ingress \
        --group-id ${SG_ID} \
        --protocol tcp \
        --port 80 \
        --cidr 0.0.0.0/0 \
        --region ${REGION} > /dev/null 2>&1 || true
    
    # Allow HTTPS
    aws ec2 authorize-security-group-ingress \
        --group-id ${SG_ID} \
        --protocol tcp \
        --port 443 \
        --cidr 0.0.0.0/0 \
        --region ${REGION} > /dev/null 2>&1 || true
    
    # Allow ASIMNEXUS API
    aws ec2 authorize-security-group-ingress \
        --group-id ${SG_ID} \
        --protocol tcp \
        --port 8000 \
        --cidr 0.0.0.0/0 \
        --region ${REGION} > /dev/null 2>&1 || true
    
    echo -e "${GREEN}✓ Security group created: ${SG_ID}${NC}"
fi

# Launch EC2 instance
echo -e "${YELLOW}Launching EC2 instance (${INSTANCE_TYPE})...${NC}"
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id ${AMI_ID} \
    --instance-type ${INSTANCE_TYPE} \
    --key-name ${KEY_NAME} \
    --security-group-ids ${SG_ID} \
    --user-data file://<(cat <<'EOF'
#!/bin/bash
# ASIMNEXUS EC2 User Data
# ======================

# Update system
apt-get update -y
apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create ASIMNEXUS directory
mkdir -p /opt/asimnexus
cd /opt/asimnexus

# Clone repository (replace with your repo)
# git clone https://github.com/yourusername/asimnexus.git .

# Start ASIMNEXUS
# docker-compose up -d

# Setup auto-start
systemctl enable docker
EOF
) \
    --region ${REGION} \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=${PROJECT_NAME}-free-tier},{Key=Project,Value=${PROJECT_NAME}}]" \
    --query 'Instances[0].InstanceId' \
    --output text)

echo -e "${GREEN}✓ Instance launched: ${INSTANCE_ID}${NC}"

# Wait for instance to be running
echo -e "${YELLOW}Waiting for instance to be running...${NC}"
aws ec2 wait instance-running --instance-ids ${INSTANCE_ID} --region ${REGION}
echo -e "${GREEN}✓ Instance is running${NC}"

# Get instance public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids ${INSTANCE_ID} \
    --region ${REGION} \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo ""
echo -e "${GREEN}==========================================${NC}"
echo -e "${GREEN}✓ AWS EC2 Free Tier Setup Complete${NC}"
echo -e "${GREEN}==========================================${NC}"
echo ""
echo "Instance Details:"
echo "  Instance ID: ${INSTANCE_ID}"
echo "  Instance Type: ${INSTANCE_TYPE} (Free Tier)"
echo "  Public IP: ${PUBLIC_IP}"
echo "  Region: ${REGION}"
echo "  SSH Command: ssh -i ${KEY_NAME}.pem ubuntu@${PUBLIC_IP}"
echo ""
echo "Free Tier Info:"
echo "  - 750 hours/month free"
echo "  - 1 vCPU, 1GB RAM"
echo "  - 30GB EBS storage"
echo "  - Cost after free tier: ~$8.50/month"
echo ""
echo "Next Steps:"
echo "  1. SSH into instance: ssh -i ${KEY_NAME}.pem ubuntu@${PUBLIC_IP}"
echo "  2. Clone ASIMNEXUS repository"
echo "  3. Run docker-compose up -d"
echo "  4. Access at http://${PUBLIC_IP}:8000"
echo ""
echo "To stop instance (save free tier hours):"
echo "  aws ec2 stop-instances --instance-ids ${INSTANCE_ID} --region ${REGION}"
echo ""
echo "To terminate instance:"
echo "  aws ec2 terminate-instances --instance-ids ${INSTANCE_ID} --region ${REGION}"
