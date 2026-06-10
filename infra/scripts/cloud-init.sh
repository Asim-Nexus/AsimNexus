
#!/bin/bash
echo "🚀 ASIMNEXUS Cloud Initialization"
echo "=================================="

# Update system
apt-get update -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Clone ASIMNEXUS
git clone https://github.com/asimnexus/asimnexus.git /app
cd /app

# Start services
docker-compose up -d

echo "✅ ASIMNEXUS deployed successfully"
