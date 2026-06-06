
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS Email MCP Connector
==============================
Model Context Protocol connector for Email services
Supports Gmail, Outlook, and generic SMTP/IMAP
Allows AI agents to send, receive, and manage emails
"""

import asyncio
import logging
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import uuid
import aiohttp
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import imaplib

logger = logging.getLogger("EmailMCP")


class EmailProvider(Enum):
    """Email service providers"""
    GMAIL = "gmail"
    OUTLOOK = "outlook"
    SMTP_IMAP = "smtp_imap"
    GENERIC = "generic"


class EmailResourceType(Enum):
    """Types of email resources"""
    MESSAGE = "message"
    THREAD = "thread"
    LABEL = "label"
    DRAFT = "draft"
    ATTACHMENT = "attachment"


@dataclass
class EmailConfig:
    """Email configuration"""
    provider: EmailProvider
    access_token: str = ""
    api_url: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    imap_host: str = ""
    imap_port: int = 993
    email_address: str = ""
    password: str = ""
    
    @classmethod
    def from_env(cls, provider: EmailProvider):
        """Load configuration from environment variables"""
        if provider == EmailProvider.GMAIL:
            return cls(
                provider=provider,
                access_token=os.getenv("GMAIL_ACCESS_TOKEN", ""),
                api_url="https://gmail.googleapis.com/gmail/v1"
            )
        elif provider == EmailProvider.OUTLOOK:
            return cls(
                provider=provider,
                access_token=os.getenv("OUTLOOK_ACCESS_TOKEN", ""),
                api_url="https://graph.microsoft.com/v1.0/me"
            )
        elif provider == EmailProvider.SMTP_IMAP:
            return cls(
                provider=provider,
                smtp_host=os.getenv("SMTP_HOST", ""),
                smtp_port=int(os.getenv("SMTP_PORT", "587")),
                imap_host=os.getenv("IMAP_HOST", ""),
                imap_port=int(os.getenv("IMAP_PORT", "993")),
                email_address=os.getenv("EMAIL_ADDRESS", ""),
                password=os.getenv("EMAIL_PASSWORD", "")
            )
        else:
            return cls(provider=provider)


@dataclass
class EmailOperation:
    """Email operation context"""
    operation_id: str
    resource_type: EmailResourceType
    action: str  # "get", "send", "delete", "list", "reply", "forward"
    message_id: str = ""
    thread_id: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EmailResult:
    """Result of email operation"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    operation: Optional[EmailOperation] = None


class EmailMCPConnector:
    """
    Email MCP Connector for agent access to email services
    Features:
    - Send emails
    - Read emails
    - Manage drafts
    - Thread management
    - Label management
    - Attachment handling
    - Multi-provider support (Gmail, Outlook, SMTP/IMAP)
    """
    
    def __init__(self, config: Optional[EmailConfig] = None):
        self.config = config or EmailConfig.from_env(EmailProvider.GMAIL)
        self.session: Optional[aiohttp.ClientSession] = None
        self.operation_history: List[EmailOperation] = []
        
        # Initialize connector
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize the Email MCP connector"""
        logger.info("🔌 Initializing Email MCP Connector...")
        logger.info("📡 Protocol: Model Context Protocol (MCP)")
        logger.info(f"🔒 Provider: {self.config.provider.value}")
        
        if self.config.provider in [EmailProvider.GMAIL, EmailProvider.OUTLOOK] and not self.config.access_token:
            logger.warning("⚠️  Access token not configured - limited access")
        
        if self.config.provider == EmailProvider.SMTP_IMAP and not self.config.email_address:
            logger.warning("⚠️  Email credentials not configured - limited access")
        
        logger.info("✅ Email MCP Connector initialized")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            headers = {
                "Authorization": f"Bearer {self.config.access_token}",
                "Content-Type": "application/json"
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session
    
    async def execute_operation(self, operation: EmailOperation) -> EmailResult:
        """
        Execute email operation
        
        Args:
            operation: Email operation context
        
        Returns:
            EmailResult with data or error
        """
        try:
            # Log operation
            self.operation_history.append(operation)
            logger.info(f"📝 Email operation: {operation.action} {operation.resource_type.value}")
            
            # Execute based on provider
            if self.config.provider == EmailProvider.GMAIL:
                result = await self._execute_gmail(operation)
            elif self.config.provider == EmailProvider.OUTLOOK:
                result = await self._execute_outlook(operation)
            elif self.config.provider == EmailProvider.SMTP_IMAP:
                result = await self._execute_smtp_imap(operation)
            else:
                result = await self._execute_generic(operation)
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Email operation error: {e}")
            return EmailResult(
                success=False,
                error=str(e),
                operation=operation
            )
    
    async def _execute_gmail(self, operation: EmailOperation) -> EmailResult:
        """Execute operation for Gmail"""
        try:
            session = await self._get_session()
            
            if operation.resource_type == EmailResourceType.MESSAGE:
                if operation.action == "list":
                    url = f"{self.config.api_url}/users/me/messages"
                    async with session.get(url, params=operation.params) as response:
                        if response.status == 200:
                            data = await response.json()
                            return EmailResult(success=True, data=data, operation=operation)
                        else:
                            error = await response.text()
                            return EmailResult(success=False, error=error, operation=operation)
                
                elif operation.action == "get":
                    message_id = operation.message_id
                    url = f"{self.config.api_url}/users/me/messages/{message_id}"
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            return EmailResult(success=True, data=data, operation=operation)
                        else:
                            error = await response.text()
                            return EmailResult(success=False, error=error, operation=operation)
                
                elif operation.action == "send":
                    url = f"{self.config.api_url}/users/me/messages/send"
                    async with session.post(url, json=operation.params) as response:
                        if response.status in [200, 201]:
                            data = await response.json()
                            return EmailResult(success=True, data=data, operation=operation)
                        else:
                            error = await response.text()
                            return EmailResult(success=False, error=error, operation=operation)
                
                elif operation.action == "delete":
                    message_id = operation.message_id
                    url = f"{self.config.api_url}/users/me/messages/{message_id}"
                    async with session.delete(url) as response:
                        if response.status == 204:
                            return EmailResult(success=True, data=None, operation=operation)
                        else:
                            error = await response.text()
                            return EmailResult(success=False, error=error, operation=operation)
            
            elif operation.resource_type == EmailResourceType.THREAD:
                if operation.action == "get":
                    thread_id = operation.thread_id
                    url = f"{self.config.api_url}/users/me/threads/{thread_id}"
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            return EmailResult(success=True, data=data, operation=operation)
                        else:
                            error = await response.text()
                            return EmailResult(success=False, error=error, operation=operation)
            
            elif operation.resource_type == EmailResourceType.DRAFT:
                if operation.action == "create":
                    url = f"{self.config.api_url}/users/me/drafts"
                    async with session.post(url, json=operation.params) as response:
                        if response.status in [200, 201]:
                            data = await response.json()
                            return EmailResult(success=True, data=data, operation=operation)
                        else:
                            error = await response.text()
                            return EmailResult(success=False, error=error, operation=operation)
            
            else:
                return EmailResult(
                    success=False,
                    error=f"Unsupported resource type for Gmail: {operation.resource_type.value}",
                    operation=operation
                )
                
        except Exception as e:
            logger.error(f"❌ Gmail operation error: {e}")
            return EmailResult(success=False, error=str(e), operation=operation)
    
    async def _execute_outlook(self, operation: EmailOperation) -> EmailResult:
        """Execute operation for Outlook"""
        try:
            session = await self._get_session()
            
            if operation.resource_type == EmailResourceType.MESSAGE:
                if operation.action == "list":
                    url = f"{self.config.api_url}/mailFolders/inbox/messages"
                    async with session.get(url, params=operation.params) as response:
                        if response.status == 200:
                            data = await response.json()
                            return EmailResult(success=True, data=data, operation=operation)
                        else:
                            error = await response.text()
                            return EmailResult(success=False, error=error, operation=operation)
                
                elif operation.action == "send":
                    url = f"{self.config.api_url}/sendMail"
                    async with session.post(url, json=operation.params) as response:
                        if response.status in [200, 202]:
                            data = await response.json()
                            return EmailResult(success=True, data=data, operation=operation)
                        else:
                            error = await response.text()
                            return EmailResult(success=False, error=error, operation=operation)
            
            else:
                return EmailResult(
                    success=False,
                    error=f"Unsupported resource type for Outlook: {operation.resource_type.value}",
                    operation=operation
                )
                
        except Exception as e:
            logger.error(f"❌ Outlook operation error: {e}")
            return EmailResult(success=False, error=str(e), operation=operation)
    
    async def _execute_smtp_imap(self, operation: EmailOperation) -> EmailResult:
        """Execute operation for SMTP/IMAP"""
        try:
            if operation.action == "send":
                return await self._send_via_smtp(operation)
            elif operation.action == "list":
                return await self._list_via_imap(operation)
            else:
                return EmailResult(
                    success=False,
                    error=f"Unsupported action for SMTP/IMAP: {operation.action}",
                    operation=operation
                )
                
        except Exception as e:
            logger.error(f"❌ SMTP/IMAP operation error: {e}")
            return EmailResult(success=False, error=str(e), operation=operation)
    
    async def _send_via_smtp(self, operation: EmailOperation) -> EmailResult:
        """Send email via SMTP"""
        try:
            to_addr = operation.params.get("to", "")
            subject = operation.params.get("subject", "")
            body = operation.params.get("body", "")
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config.email_address
            msg['To'] = to_addr
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Send via SMTP
            with smtplib.SMTP(self.config.smtp_host, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.email_address, self.config.password)
                server.send_message(msg)
            
            return EmailResult(
                success=True,
                data={"message": "Email sent successfully"},
                operation=operation
            )
                
        except Exception as e:
            logger.error(f"❌ SMTP send error: {e}")
            return EmailResult(success=False, error=str(e), operation=operation)
    
    async def _list_via_imap(self, operation: EmailOperation) -> EmailResult:
        """List emails via IMAP"""
        try:
            # Connect to IMAP
            with imaplib.IMAP4_SSL(self.config.imap_host, self.config.imap_port) as imap:
                imap.login(self.config.email_address, self.config.password)
                imap.select('INBOX')
                
                # Search for emails
                status, messages = imap.search(None, 'ALL')
                email_ids = messages[0].split()
                
                # Fetch limited number of emails
                limit = operation.params.get("limit", 10)
                emails = []
                for email_id in email_ids[-limit:]:
                    status, msg_data = imap.fetch(email_id, '(RFC822)')
                    emails.append({
                        "id": email_id.decode(),
                        "data": msg_data[0][1].decode()
                    })
                
                return EmailResult(
                    success=True,
                    data={"emails": emails, "total": len(email_ids)},
                    operation=operation
                )
                
        except Exception as e:
            logger.error(f"❌ IMAP list error: {e}")
            return EmailResult(success=False, error=str(e), operation=operation)
    
    async def _execute_generic(self, operation: EmailOperation) -> EmailResult:
        """Execute operation for generic email"""
        try:
            # Generic implementation
            logger.info("📝 Generic email operation (simulated)")
            
            return EmailResult(
                success=True,
                data={"message": "Generic email operation simulated"},
                operation=operation
            )
                
        except Exception as e:
            logger.error(f"❌ Generic email operation error: {e}")
            return EmailResult(success=False, error=str(e), operation=operation)
    
    def get_operation_history(self) -> List[EmailOperation]:
        """Get operation history"""
        return self.operation_history.copy()
    
    async def close(self) -> None:
        """Close the connector and cleanup resources"""
        if self.session and not self.session.closed:
            await self.session.close()
        logger.info("✅ Email MCP Connector closed")


# Global instances
_email_mcp_instances: Dict[EmailProvider, EmailMCPConnector] = {}


def get_email_mcp(provider: EmailProvider = EmailProvider.GMAIL) -> EmailMCPConnector:
    """Get singleton instance of Email MCP for a provider"""
    global _email_mcp_instances
    if provider not in _email_mcp_instances:
        _email_mcp_instances[provider] = EmailMCPConnector(EmailConfig.from_env(provider))
    return _email_mcp_instances[provider]


# Example usage
async def example_usage():
    """Example of how to use Email MCP"""
    mcp = get_email_mcp(EmailProvider.GMAIL)
    
    # List messages
    operation = EmailOperation(
        operation_id=f"op_{uuid.uuid4().hex[:8]}",
        resource_type=EmailResourceType.MESSAGE,
        action="list",
        params={"maxResults": 10}
    )
    
    result = await mcp.execute_operation(operation)
    print(f"Message list result: {result.success}")
    
    # Send message
    operation = EmailOperation(
        operation_id=f"op_{uuid.uuid4().hex[:8]}",
        resource_type=EmailResourceType.MESSAGE,
        action="send",
        params={
            "to": "recipient@example.com",
            "subject": "ASIMNEXUS Test Email",
            "body": "This is a test email from ASIMNEXUS"
        }
    )
    
    result = await mcp.execute_operation(operation)
    print(f"Send result: {result.success}")
    
    # Close connector
    await mcp.close()


if __name__ == "__main__":
    asyncio.run(example_usage())
