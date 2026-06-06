
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Pollinations.ai Connector
===================================
Connector for Pollinations.ai API
Provides integration with Pollinations.ai for AI image generation
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger("PollinationsConnector")

# Try to import requests
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logger.warning("requests not installed. Install with: pip install requests")


class ImageModel(Enum):
    """Pollinations.ai image models"""
    FLUX = "flux"
    TURBO = "turbo"
    SDXL = "sdxl"
    SD15 = "sd15"


class PollinationsConnector:
    """
    Pollinations.ai Connector
    
    Provides:
    - Generate images from text
    - Multiple image models
    - Custom parameters
    - Image variations
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.logger = logging.getLogger("PollinationsConnector")
        self.api_key = api_key
        self.base_url = "https://enter.pollinations.ai"
        self.default_model = ImageModel.FLUX
        
        if REQUESTS_AVAILABLE:
            self.logger.info("Pollinations.ai connector initialized")
        else:
            self.logger.warning("Pollinations.ai connector not available")
    
    def is_available(self) -> bool:
        """Check if connector is available"""
        return REQUESTS_AVAILABLE
    
    async def generate_image(
        self,
        prompt: str,
        model: Optional[ImageModel] = None,
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None,
        nologo: bool = True,
        private: bool = False
    ) -> Optional[str]:
        """
        Generate an image from text prompt
        
        Args:
            prompt: Text description of the image
            model: Image model to use
            width: Image width
            height: Image height
            seed: Random seed for reproducibility
            nologo: Remove watermark
            private: Make image private
            
        Returns:
            Image URL
        """
        if not self.is_available():
            self.logger.warning("Pollinations.ai connector not available")
            return None
        
        try:
            model = model or self.default_model
            
            # Build URL with parameters
            url = f"{self.base_url}/prompt/{prompt}"
            params = {
                "model": model.value,
                "width": width,
                "height": height,
                "nologo": str(nologo).lower(),
                "private": str(private).lower()
            }
            
            if seed is not None:
                params["seed"] = seed
            
            if self.api_key:
                params["key"] = self.api_key
            
            # Pollinations.ai returns the image directly
            response = requests.get(url, params=params, stream=True)
            response.raise_for_status()
            
            # Return the URL that was used (can be used to download)
            return response.url
            
        except Exception as e:
            self.logger.error(f"Failed to generate image: {e}")
            return None
    
    async def generate_image_url(
        self,
        prompt: str,
        model: Optional[ImageModel] = None,
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None
    ) -> Optional[str]:
        """
        Generate an image URL (without downloading)
        
        Args:
            prompt: Text description of the image
            model: Image model to use
            width: Image width
            height: Image height
            seed: Random seed
            
        Returns:
            Image URL
        """
        if not self.is_available():
            self.logger.warning("Pollinations.ai connector not available")
            return None
        
        try:
            model = model or self.default_model
            
            # Build URL with parameters
            url = f"{self.base_url}/prompt/{prompt}"
            params = {
                "model": model.value,
                "width": width,
                "height": height
            }
            
            if seed is not None:
                params["seed"] = seed
            
            if self.api_key:
                params["key"] = self.api_key
            
            # Construct full URL
            import urllib.parse
            encoded_prompt = urllib.parse.quote(prompt)
            full_url = f"{self.base_url}/prompt/{encoded_prompt}"
            
            # Add query parameters
            query_string = "&".join([f"{k}={v}" for k, v in params.items()])
            if query_string:
                full_url += f"?{query_string}"
            
            return full_url
            
        except Exception as e:
            self.logger.error(f"Failed to generate image URL: {e}")
            return None
    
    async def download_image(
        self,
        prompt: str,
        output_path: str,
        model: Optional[ImageModel] = None,
        width: int = 1024,
        height: int = 1024,
        seed: Optional[int] = None
    ) -> bool:
        """
        Generate and download an image
        
        Args:
            prompt: Text description of the image
            output_path: Path to save the image
            model: Image model to use
            width: Image width
            height: Image height
            seed: Random seed
            
        Returns:
            Success status
        """
        if not self.is_available():
            self.logger.warning("Pollinations.ai connector not available")
            return False
        
        try:
            model = model or self.default_model
            
            url = f"{self.base_url}/prompt/{prompt}"
            params = {
                "model": model.value,
                "width": width,
                "height": height
            }
            
            if seed is not None:
                params["seed"] = seed
            
            if self.api_key:
                params["key"] = self.api_key
            
            response = requests.get(url, params=params, stream=True)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.logger.info(f"Image saved to {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to download image: {e}")
            return False
    
    async def generate_variations(
        self,
        prompt: str,
        num_variations: int = 4,
        model: Optional[ImageModel] = None,
        width: int = 1024,
        height: int = 1024
    ) -> List[str]:
        """
        Generate multiple image variations
        
        Args:
            prompt: Text description of the image
            num_variations: Number of variations to generate
            model: Image model to use
            width: Image width
            height: Image height
            
        Returns:
            List of image URLs
        """
        import random
        
        urls = []
        for i in range(num_variations):
            seed = random.randint(0, 1000000)
            url = await self.generate_image_url(
                prompt,
                model=model,
                width=width,
                height=height,
                seed=seed
            )
            if url:
                urls.append(url)
        
        return urls
    
    def get_model_info(self, model: ImageModel) -> Dict:
        """Get information about a model"""
        model_info = {
            ImageModel.FLUX: {
                "name": "Flux",
                "description": "High-quality image generation model",
                "style": "photorealistic"
            },
            ImageModel.TURBO: {
                "name": "Turbo",
                "description": "Fast image generation model",
                "style": "artistic"
            },
            ImageModel.SDXL: {
                "name": "SDXL",
                "description": "Stable Diffusion XL model",
                "style": "versatile"
            },
            ImageModel.SD15: {
                "name": "SD 1.5",
                "description": "Stable Diffusion 1.5 model",
                "style": "classic"
            }
        }
        
        return model_info.get(model, {})
    
    def list_models(self) -> List[Dict]:
        """List available models"""
        return [
            {
                "id": model.value,
                "name": model.value,
                "info": self.get_model_info(model)
            }
            for model in ImageModel
        ]
    
    def get_stats(self) -> Dict:
        """Get connector statistics"""
        return {
            "available": self.is_available(),
            "requests_installed": REQUESTS_AVAILABLE,
            "api_key_configured": bool(self.api_key),
            "base_url": self.base_url,
            "default_model": self.default_model.value
        }
