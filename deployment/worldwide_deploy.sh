#!/bin/bash
# ASIMNEXUS Worldwide Deployment Script
# Deploy to cloud with worldwide access

echo "🌍 ASIMNEXUS Worldwide Deployment"
echo "====================================="

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not installed. Please install Docker first."
    exit 1
fi

# Check AWS CLI (optional)
if command -v aws &> /dev/null; then
    echo "✅ AWS CLI found"
    AWS_AVAILABLE=true
else
    echo "⚠️  AWS CLI not found (optional)"
    AWS_AVAILABLE=false
fi

# Check gcloud (optional)
if command -v gcloud &> /dev/null; then
    echo "✅ gcloud found"
    GCP_AVAILABLE=true
else
    echo "⚠️  gcloud not found (optional)"
    GCP_AVAILABLE=false
fi

# Check Azure CLI (optional)
if command -v az &> /dev/null; then
    echo "✅ Azure CLI found"
    AZURE_AVAILABLE=true
else
    echo "⚠️  Azure CLI not found (optional)"
    AZURE_AVAILABLE=false
fi

echo ""
echo "📦 Building Docker image..."
docker build -t asimnexus:latest .

echo ""
echo "🚀 Deployment Options:"
echo "1. Docker Compose (local/cloud)"
echo "2. AWS (if AWS CLI available)"
echo "3. GCP (if gcloud available)"
echo "4. Azure (if Azure CLI available)"
echo ""
echo "Select deployment option (1-4):"
read OPTION

case $OPTION in
    1)
        echo "🐳 Deploying with Docker Compose..."
        docker-compose up -d
        echo "✅ Docker Compose deployment complete"
        echo "🌐 Access at: http://localhost:8000"
        ;;
    2)
        if [ "$AWS_AVAILABLE" = true ]; then
            echo "☁️  Deploying to AWS..."
            # Build and tag for ECR
            ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
            REGION=$(aws configure get region)
            REPO_URL="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/asimnexus"
            
            # Login to ECR
            aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $REPO_URL
            
            # Tag and push
            docker tag asimnexus:latest $REPO_URL:latest
            docker push $REPO_URL:latest
            
            echo "✅ AWS deployment complete"
            echo "🌐 Configure load balancer for worldwide access"
        else
            echo "❌ AWS CLI not available"
        fi
        ;;
    3)
        if [ "$GCP_AVAILABLE" = true ]; then
            echo "☁️  Deploying to GCP..."
            PROJECT_ID=$(gcloud config get-value project)
            REPO_URL="gcr.io/${PROJECT_ID}/asimnexus"
            
            # Tag and push
            docker tag asimnexus:latest $REPO_URL:latest
            docker push $REPO_URL:latest
            
            echo "✅ GCP deployment complete"
            echo "🌐 Configure load balancer for worldwide access"
        else
            echo "❌ gcloud not available"
        fi
        ;;
    4)
        if [ "$AZURE_AVAILABLE" = true ]; then
            echo "☁️  Deploying to Azure..."
            # Get Azure registry info
            echo "Enter Azure Container Registry name:"
            read ACR_NAME
            REPO_URL="${ACR_NAME}.azurecr.io/asimnexus"
            
            # Login to ACR
            az acr login --name $ACR_NAME
            
            # Tag and push
            docker tag asimnexus:latest $REPO_URL:latest
            docker push $REPO_URL:latest
            
            echo "✅ Azure deployment complete"
            echo "🌐 Configure load balancer for worldwide access"
        else
            echo "❌ Azure CLI not available"
        fi
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo ""
echo "🌍 Worldwide Deployment Steps:"
echo "1. Deploy to multiple regions (AWS/GCP/Azure)"
echo "2. Configure global load balancer"
echo "3. Set up CDN (Cloudflare/CloudFront/Cloud CDN)"
echo "4. Configure DNS for worldwide access"
echo "5. Enable auto-scaling based on demand"
echo "6. Set up monitoring and alerting"
echo ""
echo "💰 Cost Optimization:"
echo "- Use spot/preemptible instances (90% savings)"
echo "- Auto-scale to zero when not in use"
echo "- Use free tiers when available"
echo "- Monitor and optimize resource usage"
echo ""
echo "✅ Worldwide deployment ready!"
