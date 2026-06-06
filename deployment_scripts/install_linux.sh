
#!/bin/bash
echo "🚀 ASIMNEXUS Universal Installer - Linux"
echo "========================================"

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Installing..."
    sudo apt-get update
    sudo apt-get install python3 python3-pip python3-venv -y
    echo "✅ Python3 installed successfully"
fi

# Create virtual environment
echo "📁 Creating virtual environment..."
python3 -m venv asimnexus_env
source asimnexus_env/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Set permissions
echo "🔐 Setting permissions..."
chmod +x start_asimnexus_complete.py

# Initialize ASIMNEXUS
echo "🧠 Initializing ASIMNEXUS..."
python3 main.py --init

# Start services
echo "🚀 Starting ASIMNEXUS services..."
python3 start_asimnexus_complete.py

echo "✅ ASIMNEXUS installation complete!"
echo "🌐 Access at: http://localhost:8080"
echo "🔍 Dashboard at: http://localhost:8080/frontend/dashboard.html"
