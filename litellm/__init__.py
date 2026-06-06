
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
Lightweight stub of 'litellm' for local testing within ASIM NEXUS.
Provides minimal `completion`, `acompletion`, and helper types expected
by core.litellm.asim_chaitanya_router. This stub is intentionally
simple and suitable for unit/integration tests that don't call real APIs.
"""
import asyncio
from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class Message:
    content: str


@dataclass
class Choice:
    message: Message


@dataclass
class Usage:
    total_tokens: int = 0


class Response:
    def __init__(self, text: str, tokens: int = 0):
        self.choices = [Choice(Message(text))]
        self.usage = Usage(total_tokens=tokens)


def completion(model: Optional[str] = None, messages: Optional[List[dict]] = None, max_tokens: int = 100, **kwargs) -> Response:
    """Synchronous completion stub.
    If the prompt appears to be a verification prompt, return a numeric score.
    Otherwise, return a simple echo/ack string.
    """
    text = "OK"
    if messages and isinstance(messages, list) and len(messages) > 0:
        content = messages[0].get("content", "")
        if "Verify the following response" in content or "Rate the response" in content:
            text = "0.9"
        else:
            # Echo back a short transformation for tests
            text = content[:200]
    return Response(text, tokens=min(max_tokens, 10))


async def acompletion(model: Optional[str] = None, messages: Optional[List[dict]] = None, max_tokens: int = 100, **kwargs) -> Response:
    """Asynchronous completion stub wrapping the sync completion."""
    # Simulate async behavior
    await asyncio.sleep(0)
    return completion(model=model, messages=messages, max_tokens=max_tokens, **kwargs)


def get_supported_openai_params() -> dict:
    """Return a minimal set of supported OpenAI-like parameters."""
    return {
        "temperature": [0.0, 1.0],
        "max_tokens": [1, 4096],
        "top_p": [0.0, 1.0],
        "n": [1, 10]
    }
