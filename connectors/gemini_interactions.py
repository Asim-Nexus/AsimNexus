
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Gemini Interactions API Connector
============================================
Support for Google Gemini Interactions API - unified interface for interacting with Gemini models and agents.
Features:
- Stateful and stateless conversations
- Multimodal capabilities (image, audio, video, document)
- Function calling and tools
- Deep Research Agent
- Streaming support
- Background execution
"""

import os
import logging
import base64
from typing import Dict, List, Optional, Any, Union, AsyncGenerator
from dataclasses import dataclass

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    logging.warning("google-genai package not installed. Install with: pip install google-genai>=1.55.0")

logger = logging.getLogger("ASIM_GeminiInteractions")


@dataclass
class InteractionConfig:
    """Configuration for Gemini Interactions API"""
    api_key: str
    model: str = "gemini-3-flash-preview"
    base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    temperature: float = 0.7
    max_tokens: int = 8192
    thinking_level: str = "high"  # minimal, low, medium, high
    thinking_summaries: str = "auto"  # auto, none


class GeminiInteractionsAPI:
    """
    Gemini Interactions API Connector for ASIMNEXUS
    Provides unified interface for Gemini models and agents
    """
    
    def __init__(self, config: InteractionConfig = None):
        if not GENAI_AVAILABLE:
            raise ImportError("google-genai package not installed. Install with: pip install google-genai>=1.55.0")
        
        if config is None:
            # Load from environment
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY or GOOGLE_API_KEY environment variable not set")
            config = InteractionConfig(api_key=api_key)
        
        self.config = config
        self.client = genai.Client(api_key=config.api_key)
        self.logger = logging.getLogger("ASIM_GeminiInteractions")
        
        self.logger.info(f"Gemini Interactions API initialized with model: {config.model}")
    
    def create_interaction(
        self,
        input: Union[str, List[Dict]],
        model: str = None,
        previous_interaction_id: str = None,
        tools: List[Dict] = None,
        generation_config: Dict = None,
        stream: bool = False,
        background: bool = False,
        agent: str = None,
        store: bool = True
    ) -> Any:
        """
        Create a new interaction with Gemini
        
        Args:
            input: Text prompt or list of content objects
            model: Model to use (overrides config)
            previous_interaction_id: ID of previous interaction for stateful conversation
            tools: List of function definitions for function calling
            generation_config: Generation parameters (temperature, max_tokens, etc.)
            stream: Whether to stream the response
            background: Whether to run in background mode (required for agents)
            agent: Agent to use (e.g., "deep-research-preview-04-2026")
            store: Whether to store the interaction (default: True)
        
        Returns:
            Interaction object
        """
        try:
            kwargs = {
                "input": input,
                "model": model or self.config.model,
            }
            
            if previous_interaction_id:
                kwargs["previous_interaction_id"] = previous_interaction_id
            
            if tools:
                kwargs["tools"] = tools
            
            if generation_config:
                kwargs["generation_config"] = generation_config
            else:
                kwargs["generation_config"] = {
                    "temperature": self.config.temperature,
                    "max_output_tokens": self.config.max_tokens,
                    "thinking_level": self.config.thinking_level,
                    "thinking_summaries": self.config.thinking_summaries
                }
            
            if stream:
                kwargs["stream"] = True
            
            if background:
                kwargs["background"] = True
            
            if agent:
                kwargs["agent"] = agent
            
            if not store:
                kwargs["store"] = False
            
            interaction = self.client.interactions.create(**kwargs)
            self.logger.info(f"Created interaction: {interaction.id}")
            return interaction
            
        except Exception as e:
            self.logger.error(f"Error creating interaction: {e}")
            raise
    
    def get_interaction(self, interaction_id: str, include_input: bool = False) -> Any:
        """
        Retrieve a stored interaction by ID
        
        Args:
            interaction_id: ID of the interaction to retrieve
            include_input: Whether to include the original input
        
        Returns:
            Interaction object
        """
        try:
            kwargs = {"interaction_id": interaction_id}
            if include_input:
                kwargs["include_input"] = True
            
            interaction = self.client.interactions.get(**kwargs)
            self.logger.info(f"Retrieved interaction: {interaction_id}")
            return interaction
            
        except Exception as e:
            self.logger.error(f"Error retrieving interaction: {e}")
            raise
    
    def delete_interaction(self, interaction_id: str) -> bool:
        """
        Delete a stored interaction by ID
        
        Args:
            interaction_id: ID of the interaction to delete
        
        Returns:
            True if successful
        """
        try:
            self.client.interactions.delete(interaction_id)
            self.logger.info(f"Deleted interaction: {interaction_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting interaction: {e}")
            return False
    
    def stream_interaction(
        self,
        input: Union[str, List[Dict]],
        model: str = None,
        tools: List[Dict] = None,
        generation_config: Dict = None
    ) -> AsyncGenerator:
        """
        Stream an interaction response
        
        Args:
            input: Text prompt or list of content objects
            model: Model to use (overrides config)
            tools: List of function definitions for function calling
            generation_config: Generation parameters
        
        Yields:
            Stream chunks
        """
        try:
            kwargs = {
                "input": input,
                "model": model or self.config.model,
                "stream": True
            }
            
            if tools:
                kwargs["tools"] = tools
            
            if generation_config:
                kwargs["generation_config"] = generation_config
            else:
                kwargs["generation_config"] = {
                    "temperature": self.config.temperature,
                    "max_output_tokens": self.config.max_tokens,
                    "thinking_level": self.config.thinking_level,
                    "thinking_summaries": self.config.thinking_summaries
                }
            
            stream = self.client.interactions.create(**kwargs)
            
            outputs = {}
            for chunk in stream:
                if chunk.event_type == "content.start":
                    outputs[chunk.index] = {"type": chunk.content.type}
                elif chunk.event_type == "content.delta":
                    output = outputs[chunk.index]
                    if chunk.delta.type == "text":
                        output["text"] = output.get("text", "") + chunk.delta.text
                        yield chunk.delta.text
                    elif chunk.delta.type == "thought_signature":
                        output["signature"] = chunk.delta.signature
                    elif chunk.delta.type == "thought_summary":
                        output["summary"] = output.get("summary", "") + getattr(chunk.delta.content, "text", "")
                elif chunk.event_type == "interaction.complete":
                    self.logger.info(f"Stream completed. Usage: {chunk.interaction.usage}")
                    yield {"usage": chunk.interaction.usage, "final": True}
            
        except Exception as e:
            self.logger.error(f"Error streaming interaction: {e}")
            raise
    
    def deep_research(
        self,
        query: str,
        max_duration: int = 300,
        poll_interval: int = 10
    ) -> Dict:
        """
        Use Deep Research Agent for autonomous multi-step research
        
        Args:
            query: Research query
            max_duration: Maximum time to wait in seconds
            poll_interval: Polling interval in seconds
        
        Returns:
            Research results
        """
        try:
            self.logger.info(f"Starting Deep Research for: {query}")
            
            # Start the Deep Research Agent
            initial_interaction = self.create_interaction(
                input=query,
                agent="deep-research-preview-04-2026",
                background=True
            )
            
            interaction_id = initial_interaction.id
            self.logger.info(f"Deep Research started. Interaction ID: {interaction_id}")
            
            # Poll for results
            import time
            start_time = time.time()
            
            while time.time() - start_time < max_duration:
                interaction = self.get_interaction(interaction_id)
                status = interaction.status
                
                self.logger.info(f"Deep Research status: {status}")
                
                if status == "completed":
                    self.logger.info("Deep Research completed successfully")
                    return {
                        "status": "completed",
                        "interaction_id": interaction_id,
                        "content": interaction.outputs[-1].text if interaction.outputs else "",
                        "usage": interaction.usage
                    }
                elif status in ["failed", "cancelled"]:
                    self.logger.error(f"Deep Research failed with status: {status}")
                    return {
                        "status": status,
                        "interaction_id": interaction_id,
                        "error": f"Research failed with status: {status}"
                    }
                
                time.sleep(poll_interval)
            
            # Timeout
            self.logger.warning("Deep Research timed out")
            return {
                "status": "timeout",
                "interaction_id": interaction_id,
                "error": f"Research timed out after {max_duration} seconds"
            }
            
        except Exception as e:
            self.logger.error(f"Error in deep research: {e}")
            raise
    
    def multimodal_analyze(
        self,
        content_type: str,
        content_data: Union[str, bytes],
        prompt: str = "Analyze this content",
        model: str = None
    ) -> str:
        """
        Analyze multimodal content (image, audio, video, document)
        
        Args:
            content_type: Type of content (image, audio, video, document)
            content_data: URL, base64 data, or file path
            prompt: Analysis prompt
            model: Model to use (overrides config)
        
        Returns:
            Analysis result
        """
        try:
            input_data = [
                {"type": "text", "text": prompt},
                {
                    "type": content_type,
                    "uri": content_data if isinstance(content_data, str) else f"data:{content_type};base64,{content_data}",
                    "mime_type": self._get_mime_type(content_type)
                }
            ]
            
            interaction = self.create_interaction(
                input=input_data,
                model=model or self.config.model
            )
            
            if interaction.outputs:
                return interaction.outputs[-1].text
            else:
                return "No output generated"
                
        except Exception as e:
            self.logger.error(f"Error in multimodal analysis: {e}")
            raise
    
    def _get_mime_type(self, content_type: str) -> str:
        """Get MIME type for content type"""
        mime_types = {
            "image": "image/png",
            "audio": "audio/wav",
            "video": "video/mp4",
            "document": "application/pdf"
        }
        return mime_types.get(content_type, "application/octet-stream")


# Convenience functions for easy use
def create_gemini_interactions(api_key: str = None, model: str = "gemini-3-flash-preview") -> GeminiInteractionsAPI:
    """
    Create a Gemini Interactions API client
    
    Args:
        api_key: API key (if None, loads from environment)
        model: Default model to use
    
    Returns:
        GeminiInteractionsAPI instance
    """
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    config = InteractionConfig(api_key=api_key, model=model)
    return GeminiInteractionsAPI(config)


def quick_chat(prompt: str, api_key: str = None, model: str = "gemini-3-flash-preview") -> str:
    """
    Quick single-turn chat with Gemini
    
    Args:
        prompt: User prompt
        api_key: API key (if None, loads from environment)
        model: Model to use
    
    Returns:
        Response text
    """
    client = create_gemini_interactions(api_key, model)
    interaction = client.create_interaction(input=prompt)
    
    if interaction.outputs:
        return interaction.outputs[-1].text
    else:
        return "No response generated"
