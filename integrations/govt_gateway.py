
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Government Gateway
============================
Bridge to government APIs and services
Integrates with Nagarik App and other government services
"""

import os
import logging
import json
import hashlib
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import requests

logger = logging.getLogger("GovtGateway")


class GovtService(Enum):
    """Government services"""
    NAGARIK_APP = "nagarik_app"
    CITIZENSHIP_VERIFICATION = "citizenship_verification"
    LICENSE_VERIFICATION = "license_verification"
    TAX_INFORMATION = "tax_information"
    LAND_RECORDS = "land_records"
    PUBLIC_SERVICES = "public_services"


class RequestStatus(Enum):
    """Request status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    UNAUTHORIZED = "unauthorized"


@dataclass
class GovtRequest:
    """A government API request"""
    request_id: str
    service: GovtService
    endpoint: str
    parameters: Dict[str, Any]
    status: RequestStatus
    response: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)


class GovtGateway:
    """
    Government Gateway for API Integration
    
    Provides:
    - Mock government API endpoints
    - Request authentication
    - Service integration framework
    - Response caching
    - Error handling
    
    Note: This is a mock implementation for development.
    Real government API integration requires official credentials.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("GovtGateway")
        self.requests: Dict[str, GovtRequest] = {}
        self.api_key = os.getenv("GOVT_API_KEY")
        self.base_url = os.getenv("GOVT_API_BASE_URL", "https://api.gov.example.com")
        
        # Mock database for testing
        self.mock_db = {
            "citizenship": {
                "12345678": {
                    "name": "नेपाली नागरिक",
                    "district": "काठमाडौँ",
                    "issue_date": "2020-01-15",
                    "valid": True
                }
            },
            "license": {
                "NEP123456": {
                    "name": "Driver Name",
                    "category": "Two Wheeler",
                    "expiry_date": "2025-12-31",
                    "valid": True
                }
            }
        }
        
        logger.info("✅ Government Gateway initialized")
        logger.info(f"   Base URL: {self.base_url}")
        logger.info(f"   API Key: {'Set' if self.api_key else 'Not set (using mock mode)'}")
    
    def make_request(
        self,
        service: GovtService,
        endpoint: str,
        parameters: Dict[str, Any],
        use_mock: bool = True
    ) -> Dict[str, Any]:
        """
        Make a request to government API
        
        Args:
            service: Government service
            endpoint: API endpoint
            parameters: Request parameters
            use_mock: Use mock data instead of real API
            
        Returns:
            Request result
        """
        
        request_id = f"govt_{datetime.now().timestamp()}"
        
        request = GovtRequest(
            request_id=request_id,
            service=service,
            endpoint=endpoint,
            parameters=parameters,
            status=RequestStatus.PENDING
        )
        
        self.requests[request_id] = request
        
        if use_mock or not self.api_key:
            return self._handle_mock_request(request)
        else:
            return self._handle_real_request(request)
    
    def _handle_mock_request(self, request: GovtRequest) -> Dict[str, Any]:
        """Handle mock request for testing"""
        
        request.status = RequestStatus.PROCESSING
        
        try:
            # Simulate API delay
            import time
            time.sleep(0.5)
            
            # Mock responses based on service
            if request.service == GovtService.NAGARIK_APP:
                response = self._mock_nagarik_app(request.parameters)
            elif request.service == GovtService.CITIZENSHIP_VERIFICATION:
                response = self._mock_citizenship_verification(request.parameters)
            elif request.service == GovtService.LICENSE_VERIFICATION:
                response = self._mock_license_verification(request.parameters)
            elif request.service == GovtService.PUBLIC_SERVICES:
                response = self._mock_public_services(request.parameters)
            else:
                response = {
                    "error": "Service not implemented in mock mode"
                }
            
            request.status = RequestStatus.COMPLETED
            request.response = response
            
            return {
                "success": True,
                "request_id": request.request_id,
                "service": request.service.value,
                "data": response,
                "mode": "mock"
            }
            
        except Exception as e:
            request.status = RequestStatus.FAILED
            return {
                "success": False,
                "request_id": request.request_id,
                "error": str(e),
                "mode": "mock"
            }
    
    def _handle_real_request(self, request: GovtRequest) -> Dict[str, Any]:
        """Handle real API request"""
        
        request.status = RequestStatus.PROCESSING
        
        try:
            url = f"{self.base_url}/{request.endpoint}"
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(
                url,
                json=request.parameters,
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                request.status = RequestStatus.COMPLETED
                request.response = response.json()
                
                return {
                    "success": True,
                    "request_id": request.request_id,
                    "service": request.service.value,
                    "data": response.json(),
                    "mode": "real"
                }
            elif response.status_code == 401:
                request.status = RequestStatus.UNAUTHORIZED
                return {
                    "success": False,
                    "request_id": request.request_id,
                    "error": "Unauthorized",
                    "message": "Invalid API credentials"
                }
            else:
                request.status = RequestStatus.FAILED
                return {
                    "success": False,
                    "request_id": request.request_id,
                    "error": f"API Error: {response.status_code}",
                    "message": response.text
                }
                
        except requests.Timeout:
            request.status = RequestStatus.FAILED
            return {
                "success": False,
                "request_id": request.request_id,
                "error": "Request timeout"
            }
        except Exception as e:
            request.status = RequestStatus.FAILED
            return {
                "success": False,
                "request_id": request.request_id,
                "error": str(e)
            }
    
    def _mock_nagarik_app(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Mock Nagarik App response"""
        
        citizenship_number = parameters.get("citizenship_number")
        
        if citizenship_number in self.mock_db["citizenship"]:
            data = self.mock_db["citizenship"][citizenship_number]
            return {
                "status": "valid",
                "citizenship_data": data,
                "verified_at": datetime.now().isoformat()
            }
        else:
            return {
                "status": "not_found",
                "message": "Citizenship number not found in records"
            }
    
    def _mock_citizenship_verification(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Mock citizenship verification response"""
        
        citizenship_number = parameters.get("citizenship_number")
        
        if citizenship_number in self.mock_db["citizenship"]:
            data = self.mock_db["citizenship"][citizenship_number]
            return {
                "valid": True,
                "citizenship_data": data,
                "verification_id": hashlib.sha256(citizenship_number.encode()).hexdigest()[:16]
            }
        else:
            return {
                "valid": False,
                "message": "Invalid citizenship number"
            }
    
    def _mock_license_verification(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Mock license verification response"""
        
        license_number = parameters.get("license_number")
        
        if license_number in self.mock_db["license"]:
            data = self.mock_db["license"][license_number]
            return {
                "valid": True,
                "license_data": data,
                "verification_id": hashlib.sha256(license_number.encode()).hexdigest()[:16]
            }
        else:
            return {
                "valid": False,
                "message": "Invalid license number"
            }
    
    def _mock_public_services(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Mock public services response"""
        
        service_type = parameters.get("service_type", "all")
        
        services = {
            "citizenship": "Citizenship application",
            "passport": "Passport application",
            "license": "Driving license application",
            "tax": "Tax filing",
            "land": "Land registration"
        }
        
        if service_type == "all":
            return {
                "available_services": services,
                "total_services": len(services)
            }
        elif service_type in services:
            return {
                "service": services[service_type],
                "status": "available",
                "processing_time": "7-15 working days"
            }
        else:
            return {
                "error": "Service not found"
            }
    
    def get_request_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get request status"""
        
        request = self.requests.get(request_id)
        if not request:
            return None
        
        return {
            "request_id": request.request_id,
            "service": request.service.value,
            "endpoint": request.endpoint,
            "status": request.status.value,
            "timestamp": request.timestamp.isoformat(),
            "has_response": request.response is not None
        }
    
    def list_requests(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent requests"""
        
        recent = sorted(
            self.requests.values(),
            key=lambda x: x.timestamp,
            reverse=True
        )[:limit]
        
        return [
            {
                "request_id": r.request_id,
                "service": r.service.value,
                "status": r.status.value,
                "timestamp": r.timestamp.isoformat()
            }
            for r in recent
        ]
    
    def get_available_services(self) -> List[Dict[str, Any]]:
        """Get available government services"""
        
        services = [
            {
                "service": GovtService.NAGARIK_APP.value,
                "description": "Nagarik App integration for citizen services",
                "endpoints": ["/verify/citizenship", "/verify/license"]
            },
            {
                "service": GovtService.CITIZENSHIP_VERIFICATION.value,
                "description": "Citizenship document verification",
                "endpoints": ["/verify/citizenship"]
            },
            {
                "service": GovtService.LICENSE_VERIFICATION.value,
                "description": "Driving license verification",
                "endpoints": ["/verify/license"]
            },
            {
                "service": GovtService.PUBLIC_SERVICES.value,
                "description": "Public services directory",
                "endpoints": ["/services/list"]
            }
        ]
        
        return services
    
    def get_status(self) -> Dict[str, Any]:
        """Get gateway status"""
        
        return {
            "api_key_configured": self.api_key is not None,
            "base_url": self.base_url,
            "total_requests": len(self.requests),
            "available_services": len(self.get_available_services())
        }


# Global government gateway instance
govt_gateway = GovtGateway()


def get_govt_gateway() -> GovtGateway:
    """Get global government gateway instance"""
    return govt_gateway
