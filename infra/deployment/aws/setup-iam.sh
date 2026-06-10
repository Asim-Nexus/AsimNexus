#!/bin/bash

# ASIMNEXUS AWS IAM Setup Script
# This script creates IAM roles and policies for ECS deployment

set -e

# Configuration
POLICY_NAME="AsimNexusECSDeploymentPolicy"
ROLE_NAME="AsimNexusDeploymentRole"
USER_NAME="AsimNexusDeploymentUser"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}ASIMNEXUS AWS IAM Setup${NC}"
echo "========================"

# Create IAM Policy
echo -e "${YELLOW}Creating IAM policy...${NC}"
POLICY_ARN=$(aws iam create-policy \
    --policy-name ${POLICY_NAME} \
    --policy-document file://deployment/aws/iam-policy.json \
    --query 'Policy.Arn' \
    --output text 2>/dev/null || echo "Policy may already exist")

if [ "$POLICY_ARN" = "Policy may already exist" ]; then
    POLICY_ARN=$(aws iam list-policies \
        --query "Policies[?PolicyName=='${POLICY_NAME}'].Arn" \
        --output text)
fi

echo -e "${GREEN}✓ Policy created: ${POLICY_ARN}${NC}"

# Create IAM Role for ECS
echo -e "${YELLOW}Creating IAM role for ECS...${NC}"

cat > /tmp/ecs-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": [
          "ecs-tasks.amazonaws.com",
          "ecs.amazonaws.com"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
    --role-name ${ROLE_NAME} \
    --assume-role-policy-document file:///tmp/ecs-trust-policy.json \
    2>/dev/null || echo "Role may already exist"

# Attach policy to role
aws iam attach-role-policy \
    --role-name ${ROLE_NAME} \
    --policy-arn ${POLICY_ARN}

echo -e "${GREEN}✓ ECS role created: ${ROLE_NAME}${NC}"

# Create IAM User for deployment
echo -e "${YELLOW}Creating IAM user for deployment...${NC}"

cat > /tmp/user-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-user \
    --user-name ${USER_NAME} \
    2>/dev/null || echo "User may already exist"

# Attach policy to user
aws iam attach-user-policy \
    --user-name ${USER_NAME} \
    --policy-arn ${POLICY_ARN}

echo -e "${GREEN}✓ Deployment user created: ${USER_NAME}${NC}"

# Create access key for user
echo -e "${YELLOW}Creating access key for deployment user...${NC}"
ACCESS_KEY=$(aws iam create-access-key \
    --user-name ${USER_NAME} \
    --query 'AccessKey.{AccessKeyId:AccessKeyId,SecretAccessKey:SecretAccessKey}' \
    --output json)

echo -e "${GREEN}✓ Access key created${NC}"
echo ""
echo -e "${YELLOW}================================${NC}"
echo -e "${YELLOW}ACCESS KEY DETAILS${NC}"
echo -e "${YELLOW}================================${NC}"
echo "${ACCESS_KEY}"
echo -e "${YELLOW}================================${NC}"
echo ""
echo -e "${RED}IMPORTANT: Save these credentials securely!${NC}"
echo -e "${RED}You won't see the Secret Access Key again.${NC}"
echo ""
echo "Add these to GitHub Secrets:"
echo "  AWS_ACCESS_KEY_ID: $(echo ${ACCESS_KEY} | jq -r '.AccessKeyId')"
echo "  AWS_SECRET_ACCESS_KEY: $(echo ${ACCESS_KEY} | jq -r '.SecretAccessKey')"
echo ""

# Create ECS Task Execution Role
echo -e "${YELLOW}Creating ECS Task Execution Role...${NC}"

cat > /tmp/ecs-task-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

aws iam create-role \
    --role-name ecsTaskExecutionRole \
    --assume-role-policy-document file:///tmp/ecs-task-trust-policy.json \
    2>/dev/null || echo "Task execution role may already exist"

# Attach AmazonECSTaskExecutionRolePolicy
aws iam attach-role-policy \
    --role-name ecsTaskExecutionRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy

echo -e "${GREEN}✓ ECS Task Execution Role created${NC}"

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✓ IAM Setup Complete${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Created resources:"
echo "  - Policy: ${POLICY_NAME}"
echo "  - Role: ${ROLE_NAME}"
echo "  - User: ${USER_NAME}"
echo "  - Task Execution Role: ecsTaskExecutionRole"
echo ""
echo "Next steps:"
echo "1. Save the access key credentials"
echo "2. Add them to GitHub Secrets"
echo "3. Run: bash deployment/aws/ecs-cluster-setup.sh"
