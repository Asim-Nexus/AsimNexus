
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Cloudinary Connector
===============================
Connector for Cloudinary API
Provides integration with Cloudinary for image and video storage
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import os

logger = logging.getLogger("CloudinaryConnector")

# Try to import cloudinary
try:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False
    logger.warning("cloudinary not installed. Install with: pip install cloudinary")


class ResourceType(Enum):
    """Resource types"""
    IMAGE = "image"
    VIDEO = "video"
    RAW = "raw"
    AUTO = "auto"


class CloudinaryConnector:
    """
    Cloudinary Connector
    
    Provides:
    - Upload images
    - Upload videos
    - Transform images
    - Delete resources
    - List resources
    - Get resource info
    """
    
    def __init__(self, cloud_name: Optional[str] = None, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.logger = logging.getLogger("CloudinaryConnector")
        self.cloud_name = cloud_name
        self.api_key = api_key
        self.api_secret = api_secret
        self.configured = False
        
        if CLOUDINARY_AVAILABLE and cloud_name and api_key and api_secret:
            try:
                cloudinary.config(
                    cloud_name=cloud_name,
                    api_key=api_key,
                    api_secret=api_secret
                )
                self.configured = True
                self.logger.info("Cloudinary connector initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize Cloudinary: {e}")
        elif CLOUDINARY_AVAILABLE:
            # Try to parse from connection string
            self.logger.warning("Cloudinary credentials not fully provided")
    
    def is_available(self) -> bool:
        """Check if connector is available"""
        return CLOUDINARY_AVAILABLE and self.configured
    
    async def upload_image(
        self,
        file_path: str,
        public_id: Optional[str] = None,
        folder: Optional[str] = None,
        transformation: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Upload an image
        
        Args:
            file_path: Path to image file
            public_id: Custom public ID
            folder: Folder to upload to
            transformation: Image transformation options
            
        Returns:
            Upload result
        """
        if not self.is_available():
            self.logger.warning("Cloudinary connector not available")
            return None
        
        try:
            options = {}
            if public_id:
                options["public_id"] = public_id
            if folder:
                options["folder"] = folder
            if transformation:
                options["transformation"] = transformation
            
            result = cloudinary.uploader.upload(file_path, **options)
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to upload image: {e}")
            return None
    
    async def upload_image_from_url(
        self,
        url: str,
        public_id: Optional[str] = None,
        folder: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Upload an image from URL
        
        Args:
            url: Image URL
            public_id: Custom public ID
            folder: Folder to upload to
            
        Returns:
            Upload result
        """
        if not self.is_available():
            self.logger.warning("Cloudinary connector not available")
            return None
        
        try:
            options = {}
            if public_id:
                options["public_id"] = public_id
            if folder:
                options["folder"] = folder
            
            result = cloudinary.uploader.upload(url, **options)
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to upload image from URL: {e}")
            return None
    
    async def upload_video(
        self,
        file_path: str,
        public_id: Optional[str] = None,
        folder: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Upload a video
        
        Args:
            file_path: Path to video file
            public_id: Custom public ID
            folder: Folder to upload to
            
        Returns:
            Upload result
        """
        if not self.is_available():
            self.logger.warning("Cloudinary connector not available")
            return None
        
        try:
            options = {
                "resource_type": "video"
            }
            if public_id:
                options["public_id"] = public_id
            if folder:
                options["folder"] = folder
            
            result = cloudinary.uploader.upload(file_path, **options)
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to upload video: {e}")
            return None
    
    async def delete_resource(self, public_id: str, resource_type: ResourceType = ResourceType.IMAGE) -> bool:
        """
        Delete a resource
        
        Args:
            public_id: Public ID of resource
            resource_type: Type of resource
            
        Returns:
            Success status
        """
        if not self.is_available():
            self.logger.warning("Cloudinary connector not available")
            return False
        
        try:
            result = cloudinary.api.delete_resources(
                [public_id],
                resource_type=resource_type.value
            )
            return result.get("deleted", {}).get(public_id) == "deleted"
            
        except Exception as e:
            self.logger.error(f"Failed to delete resource: {e}")
            return False
    
    async def get_resource_info(self, public_id: str, resource_type: ResourceType = ResourceType.IMAGE) -> Optional[Dict]:
        """
        Get information about a resource
        
        Args:
            public_id: Public ID of resource
            resource_type: Type of resource
            
        Returns:
            Resource information
        """
        if not self.is_available():
            self.logger.warning("Cloudinary connector not available")
            return None
        
        try:
            result = cloudinary.api.resource(
                public_id,
                resource_type=resource_type.value
            )
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to get resource info: {e}")
            return None
    
    async def list_resources(
        self,
        resource_type: ResourceType = ResourceType.IMAGE,
        max_results: int = 100,
        prefix: Optional[str] = None
    ) -> Optional[List[Dict]]:
        """
        List resources
        
        Args:
            resource_type: Type of resources
            max_results: Maximum number of results
            prefix: Filter by prefix
            
        Returns:
            List of resources
        """
        if not self.is_available():
            self.logger.warning("Cloudinary connector not available")
            return None
        
        try:
            options = {
                "resource_type": resource_type.value,
                "max_results": max_results
            }
            if prefix:
                options["prefix"] = prefix
            
            result = cloudinary.api.resources(**options)
            return result.get("resources", [])
            
        except Exception as e:
            self.logger.error(f"Failed to list resources: {e}")
            return None
    
    def generate_url(
        self,
        public_id: str,
        transformation: Optional[Dict] = None,
        resource_type: ResourceType = ResourceType.IMAGE
    ) -> str:
        """
        Generate a URL for a resource
        
        Args:
            public_id: Public ID of resource
            transformation: Transformation options
            resource_type: Type of resource
            
        Returns:
            Generated URL
        """
        if not self.is_available():
            return ""
        
        try:
            options = {}
            if transformation:
                options["transformation"] = transformation
            
            url = cloudinary.CloudinaryImage(public_id).build_url(**options)
            return url
            
        except Exception as e:
            self.logger.error(f"Failed to generate URL: {e}")
            return ""
    
    def get_stats(self) -> Dict:
        """Get connector statistics"""
        return {
            "available": self.is_available(),
            "cloudinary_installed": CLOUDINARY_AVAILABLE,
            "configured": self.configured,
            "cloud_name": self.cloud_name
        }
