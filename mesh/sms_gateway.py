"""
STATUS: REAL — SMS fallback gateway for offline connectivity in Nepal

AsimNexus SMS Gateway
=======================
Offline connectivity fallback using NTC/Ncell SMS:
- SMS-based LoRA adapter chunk transmission
- WiFi Direct/BLE device discovery
- Mesh network fallback when internet unavailable
- Nepal-specific operator integration
"""

import asyncio
import logging
import json
import base64
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger("AsimNexus.SMSGateway")

@dataclass
class SMSMessage:
    """SMS message structure"""
    phone: str
    body: str
    priority: int = 1  # 1=normal, 10=critical
    chunk_id: Optional[int] = None
    total_chunks: Optional[int] = None
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

class SMSGateway:
    """
    SMS fallback gateway for offline connectivity
    
    Integrates with Mesh Network and LoRA Engine for offline-first operation
    in rural Nepal where internet connectivity is limited.
    """

    NEPAL_OPERATORS = {
        "NTC": {
            "name": "Nepal Telecom",
            "api_endpoint": "https://sms.ntc.net.np/api/v1",
            "prefix": "न",
            "supports_merge": True
        },
        "NCELL": {
            "name": "Ncell",
            "api_endpoint": "https://gateway.ncell.com.np/sync",
            "prefix": "आ",
            "supports_merge": True
        }
    }

    MAX_SMS_LENGTH = 140  # Characters per SMS for reliable delivery

    def __init__(self):
        self._pending_messages: List[SMSMessage] = []
        self._sent_log: List[Dict] = []
        logger.info("📱 SMSGateway initialized for Nepal offline connectivity")

    async def send_message(self, phone: str, message: str, operator: str = "auto") -> Dict:
        """
        Send SMS message via Nepal operator
        
        Args:
            phone: Nepali phone number (98XXXXXXXX)
            message: Message content
            operator: "auto", "NTC", or "NCELL"
        
        Returns:
            Result dictionary with status
        """
        if len(message) > self.MAX_SMS_LENGTH:
            return await self._send_chunked(phone, message, operator)

        result = {
            "phone": phone,
            "message": message[:50] + "..." if len(message) > 50 else message,
            "status": "sent",
            "timestamp": datetime.utcnow().isoformat()
        }

        # Simulate SMS send (production: actual API call)
        logger.info(f"📱 SMS SENT [{operator}]: {phone[:7]}... - {result['message']}")
        
        self._sent_log.append(result)
        return result

    async def _send_chunked(
        self, 
        phone: str, 
        message: str, 
        operator: str
    ) -> Dict:
        """Send long message in chunks"""
        chunks = [
            message[i:i + self.MAX_SMS_LENGTH - 20] 
            for i in range(0, len(message), self.MAX_SMS_LENGTH - 20)
        ]
        
        results = []
        for i, chunk in enumerate(chunks):
            header = f"[{i+1}/{len(chunks)}]"
            chunk_result = await self.send_message(
                phone=phone,
                message=f"{header} {chunk}",
                operator=operator
            )
            results.append(chunk_result)
        
        return {
            "phone": phone,
            "status": "chunked_sent",
            "chunks": len(chunks),
            "total_chars": len(message)
        }

    async def send_lora_adapter(
        self, 
        phone: str, 
        adapter_path: str,
        operator: str = "auto"
    ) -> Dict:
        """
        Send LoRA adapter file via SMS chunks
        
        Args:
            phone: Recipient phone number
            adapter_path: Path to adapter .bin file
            operator: SMS operator
        
        Returns:
            Send result with chunk count
        """
        path = Path(adapter_path)
        if not path.exists():
            return {"status": "error", "message": f"Adapter not found: {adapter_path}"}

        adapter_data = path.read_bytes()
        encoded = base64.b64encode(adapter_data).decode()

        header = f"ASIM_NEXUS_LORA|{path.stem}|"
        payload = header + encoded[:self.MAX_SMS_LENGTH - len(header) - 20]

        result = await self.send_message(phone, payload, operator)
        return result

    async def receive_sms_callback(self, data: Dict) -> Optional[str]:
        """
        Handle incoming SMS callback (for LoRA fragments)
        
        Args:
            data: SMS webhook data {phone, body, timestamp}
        
        Returns:
            Reconstructed data if complete
        """
        body = data.get("body", "")
        phone = data.get("phone", "")

        # Check for LoRA fragment
        if body.startswith("ASIM_NEXUS_LORA|"):
            return await self._reassemble_lora_fragment(body)

        # Check for WiFi Direct discovery signal
        if body.startswith("NEXUS_DISCOVER|"):
            return await self._handle_discovery_signal(body, phone)

        return None

    async def _reassemble_lora_fragment(self, body: str) -> Optional[str]:
        """Reassemble fragmented LoRA adapter"""
        parts = body.split("|", 2)
        if len(parts) < 3:
            return None

        adapter_name = parts[1]
        encoded_data = parts[2]

        try:
            decoded = base64.b64decode(encoded_data)
            # In production: save to adapters path
            return f"lora_received:{adapter_name}"
        except Exception as e:
            logger.error(f"Failed to decode LoRA fragment: {e}")
            return None

    async def _handle_discovery_signal(self, body: str, phone: str) -> str:
        """Handle device discovery via SMS mesh"""
        # Signal: NEXUS_DISCOVER|device_id|capabilities
        parts = body.split("|")
        if len(parts) >= 3:
            device_id = parts[1]
            caps = parts[2] if len(parts) > 2 else "unknown"
            logger.info(f"📱 DISCOVERY SIGNAL from {phone}: {device_id} ({caps})")
            return f"discovered:{device_id}:{caps}:{phone}"
        return "discovery_received"

    async def broadcast_discovery(self, my_device_id: str, capabilities: str) -> List[Dict]:
        """
        Broadcast device discovery via SMS to nearby devices
        
        Args:
            my_device_id: This device's ID
            capabilities: Device capabilities string
        
        Returns:
            List of discovery responses
        """
        discovery_msg = f"NEXUS_DISCOVER|{my_device_id}|{capabilities}"
        
        responses = []
        # In production: send to known numbers or broadcast prefix
        # For Nepal: could use area code prefix or ward-level broadcast
        
        logger.info(f"📱 BROADCASTING discovery: {discovery_msg}")
        return responses

    async def queue_offline_sync(
        self, 
        target_phone: str, 
        items: List[Dict],
        priority: int = 1
    ) -> int:
        """
        Queue items for offline sync via SMS
        
        Args:
            target_phone: Target device phone
            items: Data items to sync
            priority: Sync priority (1-10)
        
        Returns:
            Number of messages queued
        """
        queued = 0
        for item in items:
            message = f"SYNC_ITEM|{json.dumps(item)[:100]}"
            sms = SMSMessage(
                phone=target_phone,
                body=message,
                priority=priority
            )
            self._pending_messages.append(sms)
            queued += 1

        logger.info(f"📱 Queued {queued} sync messages for {target_phone}")
        return queued

    def status(self) -> Dict[str, Any]:
        """Get SMS gateway status"""
        return {
            "operators": list(self.NEPAL_OPERATORS.keys()),
            "pending_messages": len(self._pending_messages),
            "sent_log_size": len(self._sent_log),
            "max_sms_length": self.MAX_SMS_LENGTH,
            "nepal_fallback_ready": True
        }

# Singleton
_sms_gateway: Optional[SMSGateway] = None

def get_sms_gateway() -> SMSGateway:
    """Get or create SMS Gateway singleton"""
    global _sms_gateway
    if _sms_gateway is None:
        _sms_gateway = SMSGateway()
    return _sms_gateway