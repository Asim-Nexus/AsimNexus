
#!/bin/bash
echo "🚀 ASIMNEXUS Universal Installer - macOS"
echo "======================================="

# Check Homebrew
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    echo "✅ Homebrew installed successfully"
fi

# Install Python
echo "📦 Installing Python..."
brew install python@3.11

# Create virtual environment
echo "📁 Creating virtual environment..."
python3.11 -m venv asimnexus_env
source asimnexus_env/bin/activate

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Initialize ASIMNEXUS
echo "🧠 Initializing ASIMNEXUS..."
python main.py --init

# Start services
echo "🚀 Starting ASIMNEXUS services..."
python start_asimnexus_complete.py

echo "✅ ASIMNEXUS installation complete!"
echo "🌐 Access at: http://localhost:8080"
echo "🔍 Dashboard at: http://localhost:8080/frontend/dashboard.html"
