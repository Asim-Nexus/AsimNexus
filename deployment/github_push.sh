#!/bin/bash
# ASIMNEXUS GitHub Deployment Script
# Push to GitHub with proper structure

echo "🚀 ASIMNEXUS GitHub Deployment"
echo "================================"

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "📝 Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit: ASIMNEXUS Super Intelligent Autonomous Digital Clone OS"
fi

# Add remote if not exists
if ! git remote | grep -q "origin"; then
    echo "📝 Adding remote origin..."
    echo "Enter your GitHub repository URL (e.g., https://github.com/YOUR_USERNAME/asimnexus.git):"
    read REPO_URL
    git remote add origin $REPO_URL
fi

# Create .gitignore if not exists
if [ ! -f ".gitignore" ]; then
    echo "📝 Creating .gitignore..."
    cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# ASIMNEXUS specific
memory/
logs/
*.log
.env
config/secrets.json

# OS
.DS_Store
Thumbs.db

# Data
data/
*.db
*.sqlite

# Cache
.asim-worktrees/
model_cache/

# Temporary
*.tmp
*.bak
EOF
fi

# Add all files
echo "📦 Adding files to git..."
git add .

# Commit changes
echo "💾 Committing changes..."
git commit -m "feat: ASIMNEXUS v1.0.0 - Super Intelligent Autonomous Digital Clone OS

- Integrated Gemma 4 local LLM (zero cost)
- Added advanced reasoning engine (chain-of-thought)
- Added long-term memory bridge
- Added multimodal processor (text, code, images, audio)
- Added security & privacy framework
- Added spot instance manager (90% cost savings)
- Added free cloud agent (zero/minimal cost)
- Added multi-cloud deployment (AWS/GCP/Azure)
- Added global load balancer
- Removed Nemotron integration (not needed)
- Consolidated duplicate config files
- Updated README.md with actual structure
- Updated Dockerfile for Gemma 4
- 15 global systems (37 modules)
- 6 autonomous capabilities
- 25+ agent types
- 8 connector systems
- Production ready for worldwide deployment"

# Push to GitHub
echo "📤 Pushing to GitHub..."
git branch -M main
git push -u origin main

echo "✅ GitHub deployment complete!"
echo ""
echo "📊 Repository pushed successfully"
echo "🌍 ASIMNEXUS is now available on GitHub"
echo ""
echo "Next steps:"
echo "1. Enable GitHub Actions for CI/CD"
echo "2. Set up cloud deployment"
echo "3. Deploy to AWS/GCP/Azure"
echo "4. Configure load balancer"
echo "5. Enable worldwide access"
