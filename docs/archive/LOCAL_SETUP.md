# ASIMNEXUS Local Setup Guide

Run ASIMNEXUS locally on your computer with frontend and backend.

## Quick Start (Windows)

```bash
# Double-click this file or run in terminal:
start-local.bat
```

## Quick Start (Linux/Mac)

```bash
# Make script executable
chmod +x start-local.sh

# Run
./start-local.sh
```

## Manual Setup

### Step 1: Install Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Download Gemma 4 Model (Optional)

```bash
# Download model (4.5GB)
bash scripts/download-gemma4-model.sh

# Or download manually from:
# https://huggingface.co/google/gemma-4-7b-it-gguf/resolve/main/gemma-4-7b-it.Q4_K_M.gguf
```

### Step 3: Configure

Edit `local-config.yaml` to customize settings:

```yaml
local_llm:
  enabled: true
  model_path: "./models/gemma-4-7b-it.Q4_K_M.gguf"
  device: "cpu"  # Change to "cuda" if you have NVIDIA GPU

api:
  port: 8000

frontend:
  enabled: true
  port: 3000
```

### Step 4: Run ASIMNEXUS

```bash
python main.py
```

## Access Points

- **Backend API:** http://localhost:8000
- **Frontend UI:** http://localhost:3000
- **WebSocket:** ws://localhost:8766
- **API Docs:** http://localhost:8000/docs

## Docker Setup

```bash
# Build image
docker build -t asimnexus:local .

# Run with Docker
docker run -d \
  --name asimnexus-local \
  -p 8000:8000 \
  -p 8766:8766 \
  -p 3000:3000 \
  -v $(pwd)/models:/app/models \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/memory:/app/memory \
  -e ASIM_ENV=local \
  asimnexus:local

# Or use docker-compose
docker-compose up
```

## Troubleshooting

### Python not found
- Install Python 3.8+ from https://python.org

### Model not found
- Run: `bash scripts/download-gemma4-model.sh`
- Or download manually to `models/` directory

### Port already in use
- Change port in `local-config.yaml`
- Or stop the service using the port

### GPU not detected
- Install CUDA: https://developer.nvidia.com/cuda-downloads
- Or use CPU mode (default)

## Features

- ✅ Local LLM (Gemma 4)
- ✅ MMMM Engine
- ✅ Life Dimensions
- ✅ Founder Clones
- ✅ Virtual Company
- ✅ Universal Chat
- ✅ Self-Learning
- ✅ Meta-Harness

## Configuration Options

See `local-config.yaml` for all available options:

- `local_llm`: Configure local LLM settings
- `api`: Backend API configuration
- `frontend`: Frontend UI configuration
- `features`: Enable/disable features
- `logging`: Logging configuration

## Next Steps

1. Open http://localhost:3000 in browser
2. Start chatting with ASIMNEXUS
3. Explore features in the dashboard
4. Check API documentation at http://localhost:8000/docs

## Support

For issues, check:
- Logs in `logs/` directory
- Configuration in `local-config.yaml`
- Documentation in `README.md`
