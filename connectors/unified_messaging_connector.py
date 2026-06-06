
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Unified Messaging Connector
=====================================
Connects WhatsApp, Telegram, Discord, Slack into one hub
All messages go through ASIM AI with 15 Founder Clones
"""

import os
import json
import asyncio
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import aiohttp

logger = logging.getLogger("ASIM_Messaging")

@dataclass
class UniversalMessage:
    """Universal message format for all platforms"""
    message_id: str
    platform: str  # 'whatsapp', 'telegram', 'discord', 'slack', 'web'
    from_user: str
    to_user: str
    content: str
    message_type: str  # 'text', 'image', 'voice', 'document', 'command'
    timestamp: str
    chat_id: str
    reply_to: Optional[str] = None
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class UnifiedMessagingConnector:
    """
    Universal messaging hub for ASIMNEXUS
    All platforms connect here and AI processes everything
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ASIM_UnifiedMessaging")
        
        # Platform connectors
        self.whatsapp_config = self._load_whatsapp_config()
        self.telegram_config = self._load_telegram_config()
        self.discord_config = self._load_discord_config()
        self.slack_config = self._load_slack_config()
        
        # Session
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Stats
        self.message_count = 0
        self.platform_stats = {
            'whatsapp': 0,
            'telegram': 0,
            'discord': 0,
            'slack': 0,
            'web': 0
        }
        
        # Initialize on first use
        self._initialized = False
        
    def _load_whatsapp_config(self) -> Dict:
        """Load WhatsApp Business API config"""
        return {
            'enabled': bool(os.getenv('WHATSAPP_API_KEY')),
            'api_key': os.getenv('WHATSAPP_API_KEY'),
            'phone_number_id': os.getenv('WHATSAPP_PHONE_ID'),
            'base_url': 'https://graph.facebook.com/v18.0',
            'webhook_secret': os.getenv('WHATSAPP_WEBHOOK_SECRET')
        }
    
    def _load_telegram_config(self) -> Dict:
        """Load Telegram Bot config"""
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN', '')
        return {
            'enabled': bool(bot_token),
            'bot_token': bot_token,
            'base_url': f"https://api.telegram.org/bot{bot_token}",
            'webhook_url': os.getenv('TELEGRAM_WEBHOOK_URL')
        }
    
    def _load_discord_config(self) -> Dict:
        """Load Discord config"""
        return {
            'enabled': bool(os.getenv('DISCORD_BOT_TOKEN')),
            'bot_token': os.getenv('DISCORD_BOT_TOKEN'),
            'application_id': os.getenv('DISCORD_APP_ID'),
            'webhook_url': os.getenv('DISCORD_WEBHOOK_URL')
        }
    
    def _load_slack_config(self) -> Dict:
        """Load Slack config"""
        return {
            'enabled': bool(os.getenv('SLACK_BOT_TOKEN')),
            'bot_token': os.getenv('SLACK_BOT_TOKEN'),
            'webhook_url': os.getenv('SLACK_WEBHOOK_URL')
        }
    
    async def initialize(self):
        """Initialize connector"""
        if self._initialized:
            return
            
        self.session = aiohttp.ClientSession()
        self._initialized = True
        
        self.logger.info("✅ Unified Messaging Connector initialized")
        self.logger.info(f"   WhatsApp: {self.whatsapp_config['enabled']}")
        self.logger.info(f"   Telegram: {self.telegram_config['enabled']}")
        self.logger.info(f"   Discord: {self.discord_config['enabled']}")
        self.logger.info(f"   Slack: {self.slack_config['enabled']}")
        
    async def process_incoming_message(self, message: UniversalMessage) -> str:
        """
        Process any incoming message from any platform
        This goes to ASIM AI Orchestrator
        """
        self.message_count += 1
        self.platform_stats[message.platform] += 1
        
        self.logger.info(f"📨 [{message.platform}] Message from {message.from_user}: {message.content[:50]}...")
        
        # Route to ASIM AI Orchestrator
        try:
            from core.multi_agent_orchestrator import MultiAgentOrchestrator
            
            orchestrator = MultiAgentOrchestrator()
            response = await orchestrator.process_user_message(
                user_id=message.from_user,
                message=message.content,
                platform=message.platform,
                message_type=message.message_type,
                context=message.metadata
            )
            
            return response
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            return f"Sorry, I encountered an error processing your message: {str(e)}"
    
    # ==================== WHATSAPP ====================
    
    async def send_whatsapp_message(self, to_number: str, message: str) -> Dict:
        """Send WhatsApp message via Business API"""
        if not self.whatsapp_config['enabled']:
            return {"error": "WhatsApp not configured"}
        
        if not self.session:
            await self.initialize()
        
        url = f"{self.whatsapp_config['base_url']}/{self.whatsapp_config['phone_number_id']}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_number,
            "type": "text",
            "text": {"body": message}
        }
        
        headers = {
            "Authorization": f"Bearer {self.whatsapp_config['api_key']}",
            "Content-Type": "application/json"
        }
        
        try:
            async with self.session.post(url, json=payload, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "success": True,
                        "message_id": data.get('messages', [{}])[0].get('id'),
                        "platform": "whatsapp"
                    }
                else:
                    error = await resp.text()
                    return {"success": False, "error": error}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def send_whatsapp_voice(self, to_number: str, audio_url: str) -> Dict:
        """Send voice message on WhatsApp"""
        if not self.whatsapp_config['enabled']:
            return {"error": "WhatsApp not configured"}
        
        url = f"{self.whatsapp_config['base_url']}/{self.whatsapp_config['phone_number_id']}/messages"
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "audio",
            "audio": {"link": audio_url}
        }
        
        headers = {
            "Authorization": f"Bearer {self.whatsapp_config['api_key']}",
            "Content-Type": "application/json"
        }
        
        async with self.session.post(url, json=payload, headers=headers) as resp:
            if resp.status == 200:
                return {"success": True, "platform": "whatsapp"}
            return {"success": False, "error": await resp.text()}
    
    # ==================== TELEGRAM ====================
    
    async def send_telegram_message(self, chat_id: str, message: str, parse_mode: str = "HTML") -> Dict:
        """Send Telegram message"""
        if not self.telegram_config['enabled']:
            return {"error": "Telegram not configured"}
        
        if not self.session:
            await self.initialize()
        
        url = f"{self.telegram_config['base_url']}/sendMessage"
        
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": parse_mode
        }
        
        try:
            async with self.session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return {
                        "success": True,
                        "message_id": data['result']['message_id'],
                        "platform": "telegram"
                    }
                else:
                    return {"success": False, "error": await resp.text()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def send_telegram_voice(self, chat_id: str, audio_file: bytes) -> Dict:
        """Send voice message on Telegram"""
        if not self.telegram_config['enabled']:
            return {"error": "Telegram not configured"}
        
        url = f"{self.telegram_config['base_url']}/sendVoice"
        
        data = aiohttp.FormData()
        data.add_field('chat_id', chat_id)
        data.add_field('voice', audio_file, filename='voice.ogg')
        
        async with self.session.post(url, data=data) as resp:
            if resp.status == 200:
                return {"success": True, "platform": "telegram"}
            return {"success": False, "error": await resp.text()}
    
    # ==================== DISCORD ====================
    
    async def send_discord_message(self, channel_id: str, message: str) -> Dict:
        """Send Discord message"""
        if not self.discord_config['enabled']:
            return {"error": "Discord not configured"}
        
        if not self.session:
            await self.initialize()
        
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
        
        headers = {
            "Authorization": f"Bot {self.discord_config['bot_token']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "content": message
        }
        
        try:
            async with self.session.post(url, json=payload, headers=headers) as resp:
                if resp.status in [200, 201]:
                    data = await resp.json()
                    return {
                        "success": True,
                        "message_id": data['id'],
                        "platform": "discord"
                    }
                else:
                    return {"success": False, "error": await resp.text()}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== SLACK ====================
    
    async def send_slack_message(self, channel: str, message: str) -> Dict:
        """Send Slack message"""
        if not self.slack_config['enabled']:
            return {"error": "Slack not configured"}
        
        if not self.session:
            await self.initialize()
        
        url = "https://slack.com/api/chat.postMessage"
        
        headers = {
            "Authorization": f"Bearer {self.slack_config['bot_token']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "channel": channel,
            "text": message
        }
        
        try:
            async with self.session.post(url, json=payload, headers=headers) as resp:
                data = await resp.json()
                if data.get('ok'):
                    return {
                        "success": True,
                        "message_id": data['ts'],
                        "platform": "slack"
                    }
                else:
                    return {"success": False, "error": data.get('error')}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # ==================== UNIVERSAL SEND ====================
    
    async def send_to_platform(self, platform: str, recipient: str, message: str, **kwargs) -> Dict:
        """
        Universal send method - works with any platform
        
        Args:
            platform: 'whatsapp', 'telegram', 'discord', 'slack', 'web'
            recipient: Phone, chat_id, channel_id, etc.
            message: Message content
        """
        if platform == 'whatsapp':
            return await self.send_whatsapp_message(recipient, message)
        elif platform == 'telegram':
            return await self.send_telegram_message(recipient, message)
        elif platform == 'discord':
            return await self.send_discord_message(recipient, message)
        elif platform == 'slack':
            return await self.send_slack_message(recipient, message)
        else:
            return {"error": f"Unknown platform: {platform}"}
    
    async def broadcast_message(self, message: str, platforms: List[str] = None) -> Dict[str, Any]:
        """
        Broadcast message to multiple platforms at once
        """
        if platforms is None:
            platforms = ['whatsapp', 'telegram', 'discord', 'slack']
        
        results = {}
        for platform in platforms:
            # Get recipients from config or database
            recipients = self._get_recipients_for_platform(platform)
            
            platform_results = []
            for recipient in recipients:
                result = await self.send_to_platform(platform, recipient, message)
                platform_results.append(result)
            
            results[platform] = platform_results
        
        return results
    
    def _get_recipients_for_platform(self, platform: str) -> List[str]:
        """Get list of recipients for a platform (from config or database)"""
        # This would come from your database
        # For now, return empty list
        return []
    
    def get_status(self) -> Dict:
        """Get connector status"""
        return {
            "initialized": self._initialized,
            "session_active": self.session is not None,
            "total_messages": self.message_count,
            "platform_stats": self.platform_stats,
            "platforms": {
                "whatsapp": self.whatsapp_config['enabled'],
                "telegram": self.telegram_config['enabled'],
                "discord": self.discord_config['enabled'],
                "slack": self.slack_config['enabled']
            }
        }


# Singleton instance
messaging_connector = UnifiedMessagingConnector()
