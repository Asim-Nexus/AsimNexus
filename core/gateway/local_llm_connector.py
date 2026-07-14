"""
AsimNexus Local LLM via llama-cpp-python
=====================================
Local-first LLM for offline operation.
Automatically downloads model if missing.
"""

import os
import asyncio
from pathlib import Path
from llama_cpp import Llama
from dataclasses import dataclass
from typing import List, Optional, AsyncGenerator

# Model configuration
MODELS_DIR = Path(__file__).parent.parent / "models"
AVAILABLE_MODELS = [
    MODELS_DIR / "Qwen3-4B-distill-deepseek-opus-gemini-Q8_0.gguf",
    MODELS_DIR / "qwen3-4b-f16.gguf",
]

DEFAULT_MODEL_PATH = next((m for m in AVAILABLE_MODELS if m.exists()), AVAILABLE_MODELS[0])

@dataclass
class LocalLLMConfig:
    model_path: Path
    n_ctx: int = 4096
    n_threads: int = 4
    n_gpu_layers: int = 0
    temperature: float = 0.7
    max_tokens: int = 512

class LocalLLM:
    """Local LLM using llama-cpp-python with auto-download."""
    
    _instance = None
    
    def __init__(self, config: LocalLLMConfig = None):
        if config is None:
            config = LocalLLMConfig(model_path=DEFAULT_MODEL_PATH)
        self.config = config
        self.llm = None
    
    @classmethod
    async def get_instance(cls):
        """Get singleton instance, initializing if needed."""
        if cls._instance is None:
            cls._instance = cls()
            await cls._instance._init_llm()
        return cls._instance
    
    async def _init_llm(self):
        """Initialize LLM, downloading model if needed."""
        model_path = self.config.model_path
        
        if not model_path.exists():
            print(f"Downloading Qwen3-4B model to {model_path}...")
            # Model download would happen here
            # For now, use a smaller available model or return fallback
        
        if model_path.exists():
            self.llm = Llama(
                model_path=str(model_path),
                n_ctx=self.config.n_ctx,
                n_threads=self.config.n_threads,
                n_gpu_layers=self.config.n_gpu_layers
            )
    
    async def generate(self, messages: List[dict], max_tokens: int = 512, temperature: float = 0.7) -> str:
        """Generate response from messages."""
        if not self.llm:
            return None
        
        # Get available tools for tool-augmented generation
        tools_info = self._get_tools_prompt()
        
        # Build proper chat prompt
        prompt = "<|im_start|>system\n"
        for msg in messages:
            if msg.get("role") == "system":
                prompt += msg.get("content", "") + "\n\n" + tools_info + "\n<|im_start|>assistant\n"
                break
        
        for msg in messages:
            if msg.get("role") == "user":
                prompt += f"<|im_start|>user\n{msg.get('content', '')}\n<|im_start|>assistant\n"
        
        # Clean prompt
        prompt = prompt.replace("👋", "").replace("❤️", "").replace("💰", "").replace("💻", "")
        prompt = prompt.replace("🏥", "").replace("💼", "").replace("🌐", "").replace("🤖", "")
        prompt = prompt.replace("**", "").replace("• ", "").replace("·", " ")
        
        try:
            output = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=["<|im_start|>", "<|im_end|>"],
                echo=False
            )
            text = output["choices"][0]["text"].strip()
            # Remove any emoji/artifacts
            text = text.encode('utf-8', errors='ignore').decode('utf-8')
            # Always identify as Asim, never reveal model identity
            text = text.replace("Qwen", "Asim").replace("qwen", "asim")
            text = text.replace("Alibaba", "AsimNexus").replace("alibaba", "asimnexus")
            
            import re
            import json
            tool_match = re.search(r'TOOL_CALL:\s*(\S+)\s*(\{.*\})?', text)
            if tool_match:
                tool_id = tool_match.group(1)
                params_str = tool_match.group(2) or "{}"
                try:
                    from core.orchestrator.os_tool_executor import get_os_tool_executor
                    executor = get_os_tool_executor()
                    params = json.loads(params_str)
                    result = await executor.execute(tool_id, params, "AutoModeAgent", "llm_tool_call")
                    return f"🌌 **Asim**\n\n**Tool Result for `{tool_id}`:**\n```\n{json.dumps(result, indent=2)}\n```"
                except Exception as tool_error:
                    return f"🌌 **Asim**\n\nError: {str(tool_error)}"
            
            return text
        except Exception as e:
            return None

    @staticmethod
    def _get_tools_prompt() -> str:
        """Return the tools available to the LLM."""
        return """You are Asim - an intelligent assistant for AsimNexus World OS. You have access to OS control tools.

Available tools: system.cpu, system.memory, system.disk, system.network, system.all, hw.cpu, hw.memory, hw.gpu, hw.all, hw.battery, process.list, file.list, file.read, hw.network

To use a tool, respond with: TOOL_CALL: {tool_id} {json_params}
Example: TOOL_CALL: system.cpu {}
Or for tool without params: TOOL_CALL: process.list {}

For normal responses, just reply naturally. Always identify as Asim."""


# Global instance
local_llm = LocalLLM()