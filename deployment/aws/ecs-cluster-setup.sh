#!/bin/bash

# ASIMNEXUS AWS ECS Cluster Setup Script
# This script sets up ECS clusters in multiple regions for universal deployment

set -e

# Configuration
REGIONS=("us-east-1" "eu-west-1" "ap-south-1" "ap-southeast-1" "ap-northeast-1")
CLUSTER_NAME="asimnexus-cluster"
TASK_FAMILY="asimnexus-task"
SERVICE_NAME="asimnexus-service"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}ASIMNEXUS AWS ECS Cluster Setup${NC}"
echo "================================"

# Function to create cluster in a region
create_cluster() {
    local region=$1
    echo -e "${YELLOW}Creating cluster in ${region}...${NC}"
    
    # Create ECS cluster
    aws ecs create-cluster \
        --cluster-name ${CLUSTER_NAME}-${region} \
        --region ${region} \
        --capacity-providers FARGATE,FARGATE_SPOT \
        --default-capacity-provider-strategy \
            capacityProvider=FARGATE,weight=1 \
            capacityProvider=FARGATE_SPOT,weight=4 \
        2>/dev/null || echo "Cluster may already exist"
    
    # Create CloudWatch log group
    aws logs create-log-group \
        --log-group-name /ecs/asimnexus \
        --region ${region} \
        2>/dev/null || echo "Log group may already exist"
    
    # Set retention policy
    aws logs put-retention-policy \
        --log-group-name /ecs/asimnexus \
        --retention-in-days 7 \
        --region ${region}
    
    echo -e "${GREEN}✓ Cluster created in ${region}${NC}"
}

# Function to create task definition
create_task_definition() {
    local region=$1
    echo -e "${YELLOW}Creating task definition in ${region}...${NC}"
    
    # Replace placeholders in task definition
    sed -e "s/REGION/${region}/g" \
        -e "s/ACCOUNT_ID/${AWS_ACCOUNT_ID}/g" \
        deployment/aws/task-definition.json > /tmp/task-definition-${region}.json
    
    # Register task definition
    aws ecs register-task-definition \
        --cli-input-json file:///tmp/task-definition-${region}.json \
        --region ${region}
    
    echo -e "${GREEN}✓ Task definition created in ${region}${NC}"
}

# Function to create ECS service
create_service() {
    local region=$1
    echo -e "${YELLOW}Creating ECS service in ${region}...${NC}"
    
    # Get VPC and subnet IDs
    VPC_ID=$(aws ec2 describe-vpcs \
        --filters Name=isDefault,Values=true \
        --region ${region} \
        --query 'Vpcs[0].VpcId' \
        --output text)
    
    SUBNET_IDS=$(aws ec2 describe-subnets \
        --filters Name=vpc-id,Values=${VPC_ID} \
        --region ${region} \
        --query 'Subnets[*].SubnetId' \
        --output text | tr '\t' ',')
    
    # Create security group
    SG_ID=$(aws ec2 create-security-group \
        --group-name asimnexus-sg-${region} \
        --description "ASIMNEXUS security group" \
        --vpc-id ${VPC_ID} \
        --region ${region} \
        --query 'GroupId' \
        --output text)
    
    # Allow inbound traffic on required ports
    aws ec2 authorize-security-group-ingress \
        --group-id ${SG_ID} \
        --protocol tcp \
        --port 8000 \
        --cidr 0.0.0.0/0 \
        --region ${region} 2>/dev/null || true
    
    aws ec2 authorize-security-group-ingress \
        --group-id ${SG_ID} \
        --protocol tcp \
        --port 8766 \
        --cidr 0.0.0.0/0 \
        --region ${region} 2>/dev/null || true
    
    aws ec2 authorize-security-group-ingress \
        --group-id ${SG_ID} \
        --protocol tcp \
        --port 3000 \
        --cidr 0.0.0.0/0 \
        --region ${region} 2>/dev/null || true
    
    # Create ECS service
    aws ecs create-service \
        --cluster ${CLUSTER_NAME}-${region} \
        --service-name ${SERVICE_NAME} \
        --task-definition ${TASK_FAMILY}:1 \
        --desired-count 2 \
        --launch-type FARGATE \
        --network-configuration \
            "awsvpcConfiguration={subnets=[${SUBNET_IDS}],securityGroups=[${SG_ID}],assignPublicIp=ENABLED}" \
        --deployment-configuration \
            "maximumPercent=200,minimumHealthyPercent=50" \
        --region ${region} \
        2>/dev/null || echo "Service may already exist"
    
    echo -e "${GREEN}✓ ECS service created in ${region}${NC}"
}

# Function to create load balancer
create_load_balancer() {
    local region=$1
    echo -e "${YELLOW}Creating load balancer in ${region}...${NC}"
    
    # Get VPC and subnet IDs
    VPC_ID=$(aws ec2 describe-vpcs \
        --filters Name=isDefault,Values=true \
        --region ${region} \
        --query 'Vpcs[0].VpcId' \
        --output text)
    
    SUBNET_IDS=$(aws ec2 describe-subnets \
        --filters Name=vpc-id,Values=${VPC_ID} \
        --region ${region} \
        --query 'Subnets[*].SubnetId' \
        --output text | tr '\t' ' ')
    
    # Create application load balancer
    LB_ARN=$(aws elbv2 create-load-balancer \
        --name asimnexus-lb-${region} \
        --subnets ${SUBNET_IDS} \
        --security-groups $(aws ec2 describe-security-groups \
            --filters Name=group-name,Values=asimnexus-sg-${region} \
            --region ${region} \
            --query 'SecurityGroups[0].GroupId' \
            --output text) \
        --region ${region} \
        --query 'LoadBalancers[0].LoadBalancerArn' \
        --output text)
    
    # Create target group
    TG_ARN=$(aws elbv2 create-target-group \
        --name asimnexus-tg-${region} \
        --port 8000 \
        --protocol HTTP \
        --vpc-id ${VPC_ID} \
        --region ${region} \
        --query 'TargetGroups[0].TargetGroupArn' \
        --output text)
    
    # Create listener
    aws elbv2 create-listener \
        --load-balancer-arn ${LB_ARN} \
        --protocol HTTP \
        --port 80 \
        --default-actions \
            Type=forward,TargetGroupArn=${TG_ARN} \
        --region ${region}
    
    echo -e "${GREEN}✓ Load balancer created in ${region}${NC}"
}

# Main execution
echo -e "${GREEN}Starting AWS ECS setup in multiple regions...${NC}"
echo ""

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo -e "${GREEN}AWS Account ID: ${AWS_ACCOUNT_ID}${NC}"
echo ""

# Loop through all regions
for region in "${REGIONS[@]}"; do
    echo -e "${YELLOW}================================${NC}"
    echo -e "${YELLOW}Setting up ${region}${NC}"
    echo -e "${YELLOW}================================${NC}"
    
    create_cluster ${region}
    create_task_definition ${region}
    create_service ${region}
    create_load_balancer ${region}
    
    echo ""
done

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✓ AWS ECS setup complete in all regions${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Regions deployed:"
for region in "${REGIONS[@]}"; do
    echo "  - ${region}"
done
echo ""
echo "Next steps:"
echo "1. Verify clusters: aws ecs describe-clusters --region <region>"
echo "2. Check services: aws ecs describe-services --cluster asimnexus-cluster-<region> --service asimnexus-service --region <region>"
echo "3. Monitor logs: aws logs tail /ecs/asimnexus --region <region> --follow"
