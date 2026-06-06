# ASIMNEXUS World OS - Step-by-Step Launch Guide

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- GPU with 12GB+ VRAM (for local LLM)
- API keys for AI providers (OpenAI, Anthropic, Google)
- Pinecone API key (for vector database)
- Cloud provider accounts (AWS/GCP/Azure) optional

---

## Step 1: Clone Repository

```bash
git clone https://github.com/your-repo/AsimNexus.git
cd AsimNexus
```

---

## Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Step 3: Configure Environment

Create `.env` file:

```bash
# AI Providers
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key

# Vector Database
PINECONE_API_KEY=your_pinecone_key
PINECONE_ENVIRONMENT=us-east-1

# Cloud Providers (optional)
AWS_ACCESS_KEY=your_aws_key
AWS_SECRET_KEY=your_aws_secret
GCP_PROJECT_ID=your_gcp_project
AZURE_SUBSCRIPTION_ID=your_azure_id
```

---

## Step 4: Initialize ASIMNEXUS

```bash
python asim.py --init
```

This will:
- Create necessary directories
- Initialize databases
- Set up configuration files
- Start core services

---

## Step 5: Start LLM Runtime (Optional)

For local LLM with GPU:

```bash
docker-compose up llm-runtime
```

For cloud LLM, skip this step.

---

## Step 6: Start ASIMNEXUS

```bash
python asim.py
```

This will:
- Initialize all 15 founder clones
- Start global systems
- Connect to AI providers
- Initialize vector database
- Start API server (if available)

---

## Step 7: Verify Installation

Check status:

```bash
python asim.py --status
```

Expected output:
```
✅ ASIMNEXUS World OS Running
✅ 15 Founder Clones Active
✅ 15 Global Systems Active
✅ 8 Life Dimensions Active
✅ AI Gateway Connected
✅ Vector Database Connected
✅ Observability Active
✅ Guardrails Active
```

---

## Step 8: Access Web UI (Optional)

If API is available:

```bash
python asim.py --web
```

Access at: `http://localhost:8000`

---

## Step 9: Test Basic Operations

```python
from asim import ASIMNEXUS

# Initialize
asim = ASIMNEXUS("test_user")

# Test AI
response = asim.universal_gateway.generate("Hello, ASIM!")
print(response)

# Test memory
asim.vector_memory.add_memory("My name is John")
results = asim.vector_memory.search_memories("John")
print(results)

# Test founder clones
status = asim.founder_clones.get_all_founders_status()
print(status)
```

---

## Step 10: Deploy to Cloud (Optional)

### AWS Deployment

```bash
cd deployment
python multicloud_deploy.py --provider aws
```

### GCP Deployment

```bash
python multicloud_deploy.py --provider gcp
```

### Azure Deployment

```bash
python multicloud_deploy.py --provider azure
```

---

## Troubleshooting

### Issue: Import errors
**Solution:** Run `pip install -r requirements.txt` again

### Issue: GPU not detected
**Solution:** Check NVIDIA drivers or use cloud LLM

### Issue: API key errors
**Solution:** Verify `.env` file has correct keys

### Issue: Database connection failed
**Solution:** Check Redis/PostgreSQL is running

### Issue: Port already in use
**Solution:** Change port in `config/` or kill process

---

## Next Steps

1. Read [USER_GUIDE.md](USER_GUIDE.md) for detailed usage
2. Read [API_DOCS.md](API_DOCS.md) for API reference
3. Read [ARCHITECTURE.md](ARCHITECTURE.md) for architecture details
4. Read [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for deployment options

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/your-repo/AsimNexus/issues
- Documentation: https://docs.asimnexus.ai
- Community: https://community.asimnexus.ai
