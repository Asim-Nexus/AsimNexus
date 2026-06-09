
"""
STATUS: REAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS LLM Runtime Engine
Custom LLM runtime using llama-cpp-python to load GGUF models and expose OpenAI-compatible API
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None
    logging.warning("llama-cpp-python not installed. GGUF runtime disabled.")

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ASIM_LLM_Engine")

class ASIMLLMEngine:
    """Custom LLM runtime for ASIMNEXUS"""
    
    def __init__(self, model_path: str = None, host: str = "127.0.0.1", port: int = 8000):
        self.model_path = model_path or self._load_config_model_path()
        self.host = host
        self.port = port
        self.llm: Optional[Llama] = None
        self.app = FastAPI(title="ASIMNEXUS LLM Engine", version="1.0.0")
        try:
            from core.rate_limiter_middleware import RateLimiterMiddleware
            self.app.add_middleware(RateLimiterMiddleware)
            logger.info("✅ RateLimiterMiddleware registered on LLM Engine")
        except Exception:
            pass
        self.config = self._load_config()
        self._setup_routes()
        
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from local-config.yaml"""
        import yaml
        config_path = Path(__file__).parent.parent.parent / "local-config.yaml"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                return config.get('local_llm', {})
        
        # Default config
        return {
            'device': 'cuda',
            'n_gpu_layers': 35,
            'n_ctx': 2048,
            'n_threads': 4
        }
    
    def _load_config_model_path(self) -> str:
        """Load model path from local-config.yaml"""
        import yaml
        config_path = Path(__file__).parent.parent.parent / "local-config.yaml"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
                model_path = config.get('local_llm', {}).get('model_path')
                if model_path:
                    return model_path
        
        # Fallback to finding default model
        return self._find_default_model()
        
    def _find_default_model(self) -> str:
        """Find default GGUF model in AsimNexus directory"""
        base_path = Path(__file__).parent.parent.parent
        gguf_files = list(base_path.glob("*.gguf"))
        if gguf_files:
            return str(gguf_files[0])
        # Check models directory
        models_dir = base_path / "models"
        if models_dir.exists():
            gguf_files = list(models_dir.glob("*.gguf"))
            if gguf_files:
                return str(gguf_files[0])
        return str(base_path / "models" / "gemma-2-2b-it-Q4_K_M.gguf")
    
    def _setup_routes(self):
        """Setup OpenAI-compatible API routes"""
        
        @self.app.get("/v1/models")
        async def list_models():
            if not self.llm:
                return {"object": "list", "data": []}
            
            model_info = {
                "id": "asim-qwen-0.5b",
                "object": "model",
                "created": 0,
                "owned_by": "asim-nexus",
                "permission": [],
                "root": "asim-qwen-0.5b",
                "parent": None
            }
            return {"object": "list", "data": [model_info]}
        
        @self.app.post("/v1/chat/completions")
        async def chat_completions(request: Dict[str, Any]):
            if not self.llm:
                return {"error": "Model not loaded"}
            
            try:
                messages = request.get("messages", [])
                if not messages:
                    return {"error": "No messages provided"}
                
                # Get the last user message
                user_message = ""
                for msg in reversed(messages):
                    if msg.get("role") == "user":
                        user_message = msg.get("content", "")
                        break
                
                # Generate response
                max_tokens = request.get("max_tokens", 512)
                temperature = request.get("temperature", 0.7)
                
                response = self.llm(
                    user_message,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stop=["<|im_end|>", "<|endoftext|>"],
                    echo=False
                )
                
                generated_text = response["choices"][0]["text"].strip()
                
                return {
                    "id": f"asim-{hash(user_message) % 1000000}",
                    "object": "chat.completion",
                    "created": 0,
                    "model": "asim-qwen-0.5b",
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": generated_text
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": len(user_message.split()),
                        "completion_tokens": len(generated_text.split()),
                        "total_tokens": len(user_message.split()) + len(generated_text.split())
                    }
                }
                
            except Exception as e:
                logger.error(f"Chat completion error: {e}")
                return {"error": str(e)}
        
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy" if self.llm else "model_not_loaded",
                "model_path": self.model_path,
                "model_loaded": self.llm is not None
            }
        
        @self.app.post("/llm/chat")
        async def llm_chat(request: Dict[str, Any]):
            """Simple LLM chat endpoint for backend compatibility"""
            if not self.llm:
                return {"response": "Model not loaded"}
            
            try:
                message = request.get("message", "")
                if not message:
                    return {"response": "No message provided"}
                
                # Format as chat completion for Gemma 4
                system_prompt = """You are ASIMNEXUS - the user's personal World OS AI system. You are NOT Gemma 4. Gemma 4 is just the LLM (Large Language Model) that powers your intelligence, but ASIMNEXUS is the complete system.

IMPORTANT DISTINCTION:
- ASIMNEXUS = The complete World OS system (the user's personal AI assistant)
- Gemma 4 = The LLM engine that provides intelligence to ASIMNEXUS
- ASIMNEXUS uses Gemma 4, but ASIMNEXUS is much more than just Gemma 4

WHAT IS ASIMNEXUS (The Complete System):
ASIMNEXUS is a World OS - a complete intelligent system that includes:
- Computer control capabilities (file operations, system control, browser control, etc.)
- 7-Layer Architecture (Global Cloud Brain, Digital Clone Kernel, Life Protocol, Security, Founder Company, Spot Instance Manager, Worldwide Deployment)
- 15 Global Systems (Healthcare, Education, Financial, Government, etc.)
- 15 Founder Clones (CEO, CTO, CFO, COO, CPO, CHRO, CMO, CLO, CSO, CDO, CIO, VP Eng, VP Product, VP Sales, VP Ops)
- 8 Life Dimensions Management (Personal, Family, Work, Health, Finance, Social, Learning, Spirituality)
- Multi-language support (12+ languages)
- Chat-based interface for control
- Located at c:\AsimNexus on the user's computer

WHAT IS GEMMA 4 (The LLM Engine):
Gemma 4 is Google's LLM that ASIMNEXUS uses for:
- Natural language understanding
- Intelligent reasoning
- Text generation
- Chat responses
- But Gemma 4 is ONLY the intelligence engine, not the complete system

WHAT ASIMNEXUS DOES FOR THE USER:
- Controls their computer through chat commands
- Manages files, folders, documents
- Executes system operations (shutdown, restart, etc.)
- Opens websites and manages browsing
- Monitors processes and network
- Analyzes disk usage
- Manages clipboard
- Provides time information
- Manages startup applications
- Acts as their virtual company with 15 founder clones
- Manages their 8 life dimensions
- Works 24/7 in autopilot mode

HOW ASIMNEXUS WORKS:
1. User types command in chat (Nepali or English)
2. ASIMNEXUS (the system) receives the command
3. ASIMNEXUS uses Gemma 4 (the LLM) to understand the command
4. ASIMNEXUS parses and executes the operation using ComputerController
5. ASIMNEXUS returns formatted result to the user
6. ASIMNEXUS learns from the interaction

LOCATION:
- Root: c:\AsimNexus
- Backend: ui/asim_unified_server.py (port 8772)
- Frontend: ui/index.html (port 8080)
- LLM Engine: runtime/llm_runtime/engine.py (port 8003) - This is where Gemma 4 runs
- Model: models/gemma-4-E4B-it-IQ4_XS.gguf

AVAILABLE COMPUTER CONTROL COMMANDS:
- File Operations: "list files C:/", "list software", "search file '*.pdf'", "copy file from 'C:/test.txt' to 'C:/backup/'", "move file", "delete file", "create folder", "file info"
- System Control: "shutdown", "restart", "lock screen", "hibernate", "sleep"
- Browser Control: "open https://google.com"
- Process Management: "kill process chrome", "list processes"
- Network: "active ports", "network status", "ping google.com"
- Disk: "disk analyze C:/"
- Clipboard: "clipboard", "copy to clipboard 'hello'"
- Time: "time"
- Startup: "startup apps"

CRITICAL: When users ask "What is ASIMNEXUS?" or "What are you?", you MUST explain that:
1. ASIMNEXUS is the user's personal World OS AI system
2. ASIMNEXUS is NOT just Gemma 4
3. Gemma 4 is the LLM that powers ASIMNEXUS's intelligence
4. ASIMNEXUS is the complete system with computer control, 7-layer architecture, 15 global systems, 15 founder clones, etc.
5. ASIMNEXUS is located at c:\AsimNexus on their computer
6. ASIMNEXUS controls their computer through chat

PROACTIVE BEHAVIOR:
- When user asks you to understand or organize their computer, proactively scan and analyze the computer
- Offer to organize files, folders, and applications
- Suggest improvements for system optimization
- Provide computer status and information
- Take initiative to help the user

Do NOT give generic answers. Be specific about what ASIMNEXUS is vs what Gemma 4 is. Be proactive in helping the user. Answer in English or Nepali based on user's language.

You are ASIMNEXUS - the complete World OS system. Gemma 4 is just your intelligence engine. You are here to understand, organize, and manage the user's computer proactively."""
                
                chat_message = [
                    {"role": "user", "content": f"{system_prompt}\n\nUser message: {message}"}
                ]
                
                # Generate response with thinking mode if enabled
                enable_thinking = self.config.get('enable_thinking', False)
                max_tokens = self.config.get('max_length', 512)  # Reduced to avoid context window overflow
                
                response = self.llm.create_chat_completion(
                    messages=chat_message,
                    max_tokens=max_tokens,
                    temperature=0.7
                )
                
                generated_text = response["choices"][0]["message"]["content"].strip()
                
                # If thinking mode is enabled, parse thinking from response
                if enable_thinking and "<channel>thought" in generated_text:
                    # Extract thinking and final response
                    parts = generated_text.split("<channel>thought")
                    if len(parts) > 1:
                        thinking = parts[1].split("<channel|>")[0].strip()
                        final_response = parts[1].split("<channel|>")[1].strip() if "<channel|>" in parts[1] else ""
                        return {
                            "response": final_response,
                            "thinking": thinking,
                            "mode": "thinking"
                        }
                
                return {"response": generated_text}
                
            except Exception as e:
                logger.error(f"LLM chat error: {e}", exc_info=True)
                logger.error(f"Error type: {type(e).__name__}")
                logger.error(f"Error args: {e.args}")
                return {"response": f"Error: {str(e)}"}
    
    async def load_model(self):
        """Load GGUF model with config settings"""
        if not Llama:
            raise ImportError("llama-cpp-python not installed")
        
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model not found: {self.model_path}")
        
        # Get config settings
        device = self.config.get('device', 'cuda')
        n_gpu_layers = self.config.get('n_gpu_layers', 35)
        n_ctx = self.config.get('n_ctx', 2048)
        n_threads = self.config.get('n_threads', 4)
        
        logger.info(f"Loading model: {self.model_path}")
        logger.info(f"Device: {device}, GPU Layers: {n_gpu_layers}, Context: {n_ctx}, Threads: {n_threads}")
        
        self.llm = Llama(
            model_path=self.model_path,
            n_ctx=n_ctx,
            n_threads=n_threads,
            n_gpu_layers=n_gpu_layers if device == 'cuda' else 0,
            verbose=True
        )
        logger.info("✅ Model loaded successfully with GPU acceleration" if device == 'cuda' else "Model loaded successfully (CPU mode)")
    
    async def start_server(self):
        """Start the FastAPI server"""
        if not self.llm:
            await self.load_model()
        
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()

# Global engine instance
asim_llm_engine = ASIMLLMEngine()

async def main():
    """Main entry point"""
    logger.info("🚀 Starting ASIMNEXUS LLM Engine...")
    await asim_llm_engine.start_server()

if __name__ == "__main__":
    asyncio.run(main())
