
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS GitHub MCP Connector
================================
Model Context Protocol connector for GitHub
Allows AI agents to interact with GitHub repositories, issues, PRs, and more
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

logger = logging.getLogger("GitHubMCP")


class GitHubResourceType(Enum):
    """Types of GitHub resources"""
    REPOSITORY = "repository"
    ISSUE = "issue"
    PULL_REQUEST = "pull_request"
    COMMIT = "commit"
    BRANCH = "branch"
    FILE = "file"
    RELEASE = "release"
    ACTION = "action"


@dataclass
class GitHubConfig:
    """GitHub configuration"""
    api_token: str
    api_url: str = "https://api.github.com"
    default_owner: str = ""
    default_repo: str = ""
    
    @classmethod
    def from_env(cls):
        """Load configuration from environment variables"""
        return cls(
            api_token=os.getenv("GITHUB_TOKEN", ""),
            default_owner=os.getenv("GITHUB_DEFAULT_OWNER", ""),
            default_repo=os.getenv("GITHUB_DEFAULT_REPO", "")
        )


@dataclass
class GitHubOperation:
    """GitHub operation context"""
    operation_id: str
    resource_type: GitHubResourceType
    action: str  # "get", "create", "update", "delete", "list"
    owner: str
    repo: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GitHubResult:
    """Result of GitHub operation"""
    success: bool
    data: Any = None
    error: Optional[str] = None
    operation: Optional[GitHubOperation] = None
    rate_limit_remaining: Optional[int] = None


class GitHubMCPConnector:
    """
    GitHub MCP Connector for agent access to GitHub
    Features:
    - Repository management
    - Issue and PR operations
    - File operations
    - Branch management
    - Actions integration
    - Rate limit handling
    """
    
    def __init__(self, config: Optional[GitHubConfig] = None):
        self.config = config or GitHubConfig.from_env()
        self.session: Optional[aiohttp.ClientSession] = None
        self.operation_history: List[GitHubOperation] = []
        self.rate_limit_remaining = 5000
        
        # Initialize connector
        self._initialize()
    
    def _initialize(self) -> None:
        """Initialize the GitHub MCP connector"""
        logger.info("🔌 Initializing GitHub MCP Connector...")
        logger.info("📡 Protocol: Model Context Protocol (MCP)")
        logger.info("🔒 Security: Token-based authentication")
        
        if not self.config.api_token:
            logger.warning("⚠️  GitHub token not configured - limited access")
        
        logger.info("✅ GitHub MCP Connector initialized")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self.session is None or self.session.closed:
            headers = {
                "Authorization": f"token {self.config.api_token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "ASIMNEXUS-GitHub-MCP"
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session
    
    async def execute_operation(self, operation: GitHubOperation) -> GitHubResult:
        """
        Execute GitHub operation
        
        Args:
            operation: GitHub operation context
        
        Returns:
            GitHubResult with data or error
        """
        try:
            # Log operation
            self.operation_history.append(operation)
            logger.info(f"📝 GitHub operation: {operation.action} {operation.resource_type.value}")
            
            # Check rate limit
            if self.rate_limit_remaining <= 10:
                logger.warning("⚠️  GitHub rate limit nearly exhausted")
                return GitHubResult(
                    success=False,
                    error="Rate limit nearly exhausted",
                    operation=operation,
                    rate_limit_remaining=self.rate_limit_remaining
                )
            
            # Execute based on resource type and action
            if operation.resource_type == GitHubResourceType.REPOSITORY:
                result = await self._handle_repository(operation)
            elif operation.resource_type == GitHubResourceType.ISSUE:
                result = await self._handle_issue(operation)
            elif operation.resource_type == GitHubResourceType.PULL_REQUEST:
                result = await self._handle_pull_request(operation)
            elif operation.resource_type == GitHubResourceType.FILE:
                result = await self._handle_file(operation)
            elif operation.resource_type == GitHubResourceType.BRANCH:
                result = await self._handle_branch(operation)
            elif operation.resource_type == GitHubResourceType.COMMIT:
                result = await self._handle_commit(operation)
            elif operation.resource_type == GitHubResourceType.RELEASE:
                result = await self._handle_release(operation)
            elif operation.resource_type == GitHubResourceType.ACTION:
                result = await self._handle_action(operation)
            else:
                result = GitHubResult(
                    success=False,
                    error=f"Unsupported resource type: {operation.resource_type.value}",
                    operation=operation
                )
            
            result.rate_limit_remaining = self.rate_limit_remaining
            return result
            
        except Exception as e:
            logger.error(f"❌ GitHub operation error: {e}")
            return GitHubResult(
                success=False,
                error=str(e),
                operation=operation,
                rate_limit_remaining=self.rate_limit_remaining
            )
    
    async def _handle_repository(self, operation: GitHubOperation) -> GitHubResult:
        """Handle repository operations"""
        try:
            url = f"{self.config.api_url}/repos/{operation.owner}/{operation.repo}"
            session = await self._get_session()
            
            if operation.action == "get":
                async with session.get(url) as response:
                    self._update_rate_limit(response)
                    if response.status == 200:
                        data = await response.json()
                        return GitHubResult(success=True, data=data, operation=operation)
                    else:
                        error = await response.text()
                        return GitHubResult(success=False, error=error, operation=operation)
            
            elif operation.action == "list":
                url = f"{self.config.api_url}/users/{operation.owner}/repos"
                async with session.get(url) as response:
                    self._update_rate_limit(response)
                    if response.status == 200:
                        data = await response.json()
                        return GitHubResult(success=True, data=data, operation=operation)
                    else:
                        error = await response.text()
                        return GitHubResult(success=False, error=error, operation=operation)
            
            else:
                return GitHubResult(
                    success=False,
                    error=f"Unsupported action for repository: {operation.action}",
                    operation=operation
                )
                
        except Exception as e:
            logger.error(f"❌ Repository operation error: {e}")
            return GitHubResult(success=False, error=str(e), operation=operation)
    
    async def _handle_issue(self, operation: GitHubOperation) -> GitHubResult:
        """Handle issue operations"""
        try:
            url = f"{self.config.api_url}/repos/{operation.owner}/{operation.repo}/issues"
            session = await self._get_session()
            
            if operation.action == "list":
                async with session.get(url) as response:
                    self._update_rate_limit(response)
                    if response.status == 200:
                        data = await response.json()
                        return GitHubResult(success=True, data=data, operation=operation)
                    else:
                        error = await response.text()
                        return GitHubResult(success=False, error=error, operation=operation)
            
            elif operation.action == "create":
                async with session.post(url, json=operation.params) as response:
                    self._update_rate_limit(response)
                    if response.status in [200, 201]:
                        data = await response.json()
                        return GitHubResult(success=True, data=data, operation=operation)
                    else:
                        error = await response.text()
                        return GitHubResult(success=False, error=error, operation=operation)
            
            elif operation.action == "get":
                issue_number = operation.params.get("number")
                url = f"{self.config.api_url}/repos/{operation.owner}/{operation.repo}/issues/{issue_number}"
                async with session.get(url) as response:
                    self._update_rate_limit(response)
                    if response.status == 200:
                        data = await response.json()
                        return GitHubResult(success=True, data=data, operation=operation)
                    else:
                        error = await response.text()
                        return GitHubResult(success=False, error=error, operation=operation)
            
            else:
                return GitHubResult(
                    success=False,
                    error=f"Unsupported action for issue: {operation.action}",
                    operation=operation
                )
                
        except Exception as e:
            logger.error(f"❌ Issue operation error: {e}")
            return GitHubResult(success=False, error=str(e), operation=operation)
    
    async def _handle_pull_request(self, operation: GitHubOperation) -> GitHubResult:
        """Handle pull request operations"""
        try:
            url = f"{self.config.api_url}/repos/{operation.owner}/{operation.repo}/pulls"
            session = await self._get_session()
            
            if operation.action == "list":
                async with session.get(url) as response:
                    self._update_rate_limit(response)
                    if response.status == 200:
                        data = await response.json()
                        return GitHubResult(success=True, data=data, operation=operation)
                    else:
                        error = await response.text()
                        return GitHubResult(success=False, error=error, operation=operation)
            
            elif operation.action == "create":
                async with session.post(url, json=operation.params) as response:
                    self._update_rate_limit(response)
                    if response.status in [200, 201]:
                        data = await response.json()
                        return GitHubResult(success=True, data=data, operation=operation)
                    else:
                        error = await response.text()
                        return GitHubResult(success=False, error=error, operation=operation)
            
            else:
                return GitHubResult(
                    success=False,
                    error=f"Unsupported action for pull request: {operation.action}",
                    operation=operation
                )
                
        except Exception as e:
            logger.error(f"❌ Pull request operation error: {e}")
            return GitHubResult(success=False, error=str(e), operation=operation)
    
    async def _handle_file(self, operation: GitHubOperation) -> GitHubResult:
        """Handle file operations"""
        try:
            path = operation.params.get("path", "")
            url = f"{self.config.api_url}/repos/{operation.owner}/{operation.repo}/contents/{path}"
            session = await self._get_session()
            
            if operation.action == "get":
                async with session.get(url) as response:
                    self._update_rate_limit(response)
                    if response.status == 200:
                        data = await response.json()
                        return GitHubResult(success=True, data=data, operation=operation)
                    else:
                        error = await response.text()
                        return GitHubResult(success=False, error=error, operation=operation)
            
            elif operation.action == "create" or operation.action == "update":
                async with session.put(url, json=operation.params) as response:
                    self._update_rate_limit(response)
                    if response.status in [200, 201]:
                        data = await response.json()
                        return GitHubResult(success=True, data=data, operation=operation)
                    else:
                        error = await response.text()
                        return GitHubResult(success=False, error=error, operation=operation)
            
            elif operation.action == "delete":
                async with session.delete(url, json=operation.params) as response:
                    self._update_rate_limit(response)
                    if response.status == 200:
                        data = await response.json()
                        return GitHubResult(success=True, data=data, operation=operation)
                    else:
                        error = await response.text()
                        return GitHubResult(success=False, error=error, operation=operation)
            
            else:
                return GitHubResult(
                    success=False,
                    error=f"Unsupported action for file: {operation.action}",
                    operation=operation
                )
                
        except Exception as e:
            logger.error(f"❌ File operation error: {e}")
            return GitHubResult(success=False, error=str(e), operation=operation)
    
    async def _handle_branch(self, operation: GitHubOperation) -> GitHubResult:
        """Handle branch operations"""
        try:
            url = f"{self.config.api_url}/repos/{operation.owner}/{operation.repo}/branches"
            session = await self._get_session()
            
            if operation.action == "list":
                async with session.get(url) as response:
                    self._update_rate_limit(response)
                    if response.status == 200:
                        data = await response.json()
                        return GitHubResult(success=True, data=data, operation=operation)
                    else:
                        error = await response.text()
                        return GitHubResult(success=False, error=error, operation=operation)
            
            elif operation.action == "create":
                url = f"{self.config.api_url}/repos/{operation.owner}/{operation.repo}/git/refs"
                async with session.post(url, json=operation.params) as response:
                    self._update_rate_limit(response)
                    if response.status in [200, 201]:
                        data = await response.json()
                        return GitHubResult(success=True, data=data, operation=operation)
                    else:
                        error = await response.text()
                        return GitHubResult(success=False, error=error, operation=operation)
            
            else:
                return GitHubResult(
                    success=False,
                    error=f"Unsupported action for branch: {operation.action}",
                    operation=operation
                )
                
        except Exception as e:
            logger.error(f"❌ Branch operation error: {e}")
            return GitHubResult(success=False, error=str(e), operation=operation)
    
    async def _handle_commit(self, operation: GitHubOperation) -> GitHubResult:
        """Handle commit operations"""
        try:
            url = f"{self.config.api_url}/repos/{operation.owner}/{operation.repo}/commits"
            session = await self._get_session()
            
            if operation.action == "list":
                async with session.get(url) as response:
                    self._update_rate_limit(response)
                    if response.status == 200:
                        data = await response.json()
                        return GitHubResult(success=True, data=data, operation=operation)
                    else:
                        error = await response.text()
                        return GitHubResult(success=False, error=error, operation=operation)
            
            elif operation.action == "get":
                sha = operation.params.get("sha")
                url = f"{self.config.api_url}/repos/{operation.owner}/{operation.repo}/commits/{sha}"
                async with session.get(url) as response:
                    self._update_rate_limit(response)
                    if response.status == 200:
                        data = await response.json()
                        return GitHubResult(success=True, data=data, operation=operation)
                    else:
                        error = await response.text()
                        return GitHubResult(success=False, error=error, operation=operation)
            
            else:
                return GitHubResult(
                    success=False,
                    error=f"Unsupported action for commit: {operation.action}",
                    operation=operation
                )
                
        except Exception as e:
            logger.error(f"❌ Commit operation error: {e}")
            return GitHubResult(success=False, error=str(e), operation=operation)
    
    async def _handle_release(self, operation: GitHubOperation) -> GitHubResult:
        """Handle release operations"""
        try:
            url = f"{self.config.api_url}/repos/{operation.owner}/{operation.repo}/releases"
            session = await self._get_session()
            
            if operation.action == "list":
                async with session.get(url) as response:
                    self._update_rate_limit(response)
                    if response.status == 200:
                        data = await response.json()
                        return GitHubResult(success=True, data=data, operation=operation)
                    else:
                        error = await response.text()
                        return GitHubResult(success=False, error=error, operation=operation)
            
            elif operation.action == "create":
                async with session.post(url, json=operation.params) as response:
                    self._update_rate_limit(response)
                    if response.status in [200, 201]:
                        data = await response.json()
                        return GitHubResult(success=True, data=data, operation=operation)
                    else:
                        error = await response.text()
                        return GitHubResult(success=False, error=error, operation=operation)
            
            else:
                return GitHubResult(
                    success=False,
                    error=f"Unsupported action for release: {operation.action}",
                    operation=operation
                )
                
        except Exception as e:
            logger.error(f"❌ Release operation error: {e}")
            return GitHubResult(success=False, error=str(e), operation=operation)
    
    async def _handle_action(self, operation: GitHubOperation) -> GitHubResult:
        """Handle GitHub Actions operations"""
        try:
            url = f"{self.config.api_url}/repos/{operation.owner}/{operation.repo}/actions"
            session = await self._get_session()
            
            if operation.action == "list":
                async with session.get(url) as response:
                    self._update_rate_limit(response)
                    if response.status == 200:
                        data = await response.json()
                        return GitHubResult(success=True, data=data, operation=operation)
                    else:
                        error = await response.text()
                        return GitHubResult(success=False, error=error, operation=operation)
            
            else:
                return GitHubResult(
                    success=False,
                    error=f"Unsupported action for actions: {operation.action}",
                    operation=operation
                )
                
        except Exception as e:
            logger.error(f"❌ Actions operation error: {e}")
            return GitHubResult(success=False, error=str(e), operation=operation)
    
    def _update_rate_limit(self, response: aiohttp.ClientResponse) -> None:
        """Update rate limit from response headers"""
        remaining = response.headers.get("X-RateLimit-Remaining")
        if remaining:
            self.rate_limit_remaining = int(remaining)
    
    def get_operation_history(self) -> List[GitHubOperation]:
        """Get operation history"""
        return self.operation_history.copy()
    
    async def close(self) -> None:
        """Close the connector and cleanup resources"""
        if self.session and not self.session.closed:
            await self.session.close()
        logger.info("✅ GitHub MCP Connector closed")


# Global instance
_github_mcp: Optional[GitHubMCPConnector] = None


def get_github_mcp() -> GitHubMCPConnector:
    """Get singleton instance of GitHub MCP"""
    global _github_mcp
    if _github_mcp is None:
        _github_mcp = GitHubMCPConnector()
    return _github_mcp


# Example usage
async def example_usage():
    """Example of how to use GitHub MCP"""
    mcp = get_github_mcp()
    
    # List repositories
    operation = GitHubOperation(
        operation_id=f"op_{uuid.uuid4().hex[:8]}",
        resource_type=GitHubResourceType.REPOSITORY,
        action="list",
        owner="octocat",
        repo=""
    )
    
    result = await mcp.execute_operation(operation)
    print(f"Repository list result: {result.success}")
    
    # List issues
    operation = GitHubOperation(
        operation_id=f"op_{uuid.uuid4().hex[:8]}",
        resource_type=GitHubResourceType.ISSUE,
        action="list",
        owner="octocat",
        repo="Hello-World"
    )
    
    result = await mcp.execute_operation(operation)
    print(f"Issue list result: {result.success}")
    
    # Close connector
    await mcp.close()


if __name__ == "__main__":
    asyncio.run(example_usage())
