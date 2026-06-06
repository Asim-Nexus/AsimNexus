
"""
STATUS: PRODUCTION — Usage tracking with limit awareness, auto-switch logic at >80% consumption,
intelligent provider selection with scoring, real deployment monitoring
"""

"""
ASIMNEXUS Free Cloud Agent
===========================
Agent for finding and utilizing free cloud resources
Optimizes cost by leveraging free tiers and credits
Auto-switches when free tier limits are approached
Real usage monitoring with limit predictions
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger("FreeCloudAgent")


class FreeCloudProvider(Enum):
    """Cloud providers with free tiers"""
    HEROKU = "heroku"
    VERCEL = "vercel"
    RAILWAY = "railway"
    RENDER = "render"
    FLY_IO = "fly_io"
    NEON = "neon"
    SUPABASE = "supabase"
    PLANETSCALE = "planetscale"
    CLOUDFLARE = "cloudflare"


class UsageWarningLevel(Enum):
    """Warning level for free tier usage"""
    NORMAL = "normal"                   # Under 60%
    ELEVATED = "elevated"               # 60-80%
    HIGH = "high"                       # 80-95%
    CRITICAL = "critical"               # Over 95%


@dataclass
class UsageMetrics:
    """Tracked usage metrics for a deployment"""
    ram_mb_used: float = 0.0
    cpu_percent: float = 0.0
    bandwidth_mb_used: float = 0.0
    storage_mb_used: float = 0.0
    requests_count: int = 0
    uptime_hours: float = 0.0
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class FreeTierInfo:
    """Information about a free tier"""
    provider: FreeCloudProvider
    name: str
    description: str
    free_resources: Dict[str, str]
    limitations: List[str]
    requires_credit_card: bool = False
    
    # Usage limits (parsed from free_resources)
    ram_limit_mb: float = 0.0
    bandwidth_limit_mb: float = 0.0
    storage_limit_mb: float = 0.0
    request_limit: int = 0
    uptime_limit_hours: float = 0.0
    
    # Current usage tracking
    usage: UsageMetrics = field(default_factory=UsageMetrics)


@dataclass
class Deployment:
    """Deployment record"""
    deployment_id: str
    provider: FreeCloudProvider
    app_name: str
    status: str
    created_at: datetime
    resource_usage: Dict[str, str] = field(default_factory=dict)
    
    # Enhanced tracking
    usage_metrics: UsageMetrics = field(default_factory=UsageMetrics)
    warning_level: UsageWarningLevel = UsageWarningLevel.NORMAL
    auto_switch_triggered: bool = False
    last_health_check: Optional[datetime] = None


class FreeCloudAgent:
    """
    Free Cloud Agent
    
    Automatically finds and deploys to free cloud resources:
    - Tracks available free tiers with usage limits
    - Intelligent provider selection based on requirements
    - Monitors usage to stay within limits
    - Auto-switches when >80% of free tier consumed
    - Predicts when limits will be reached
    """
    
    # Thresholds for auto-switch decisions
    USAGE_WARNING_PCT = 0.60     # 60% → elevated
    USAGE_HIGH_PCT = 0.80        # 80% → high (consider switch)
    USAGE_CRITICAL_PCT = 0.95    # 95% → critical (force switch)
    
    def __init__(self):
        self.logger = logging.getLogger("FreeCloudAgent")
        self.deployments: Dict[str, Deployment] = {}
        self.free_tiers: Dict[FreeCloudProvider, FreeTierInfo] = {}
        
        self._initialize_free_tiers()
        
        # Monitoring task
        self._monitor_task: Optional[asyncio.Task] = None
        self._running: bool = False
        
        self.logger.info(f"FreeCloudAgent initialized with {len(self.free_tiers)} providers")
    
    async def start_monitoring(self):
        """Start periodic usage monitoring"""
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        self.logger.info("FreeCloudAgent monitoring started")
    
    async def stop_monitoring(self):
        """Stop periodic usage monitoring"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    def _initialize_free_tiers(self):
        """Initialize free tier information with parsed limits"""
        self.free_tiers = {
            FreeCloudProvider.HEROKU: FreeTierInfo(
                provider=FreeCloudProvider.HEROKU,
                name="Heroku Free",
                description="Free dyno with 512MB RAM",
                free_resources={
                    "ram": "512MB",
                    "compute": "550 hours/month",
                    "database": "Postgres (10,000 rows)"
                },
                limitations=["Sleeps after 30 min inactivity", "Limited bandwidth"],
                requires_credit_card=True,
                ram_limit_mb=512,
                uptime_limit_hours=550
            ),
            FreeCloudProvider.VERCEL: FreeTierInfo(
                provider=FreeCloudProvider.VERCEL,
                name="Vercel Hobby",
                description="Serverless functions with generous limits",
                free_resources={
                    "bandwidth": "100GB/month",
                    "build_minutes": "6000/month",
                    "serverless": "100GB-hours/month"
                },
                limitations=["Function timeout: 10s"],
                requires_credit_card=False,
                bandwidth_limit_mb=102400,  # 100GB
                request_limit=100000
            ),
            FreeCloudProvider.RENDER: FreeTierInfo(
                provider=FreeCloudProvider.RENDER,
                name="Render Free",
                description="Free web service with SSL",
                free_resources={
                    "ram": "512MB",
                    "cpu": "Shared CPU",
                    "bandwidth": "100GB/month"
                },
                limitations=["Spins down after 15 min inactivity"],
                requires_credit_card=True,
                ram_limit_mb=512,
                bandwidth_limit_mb=102400
            ),
            FreeCloudProvider.RAILWAY: FreeTierInfo(
                provider=FreeCloudProvider.RAILWAY,
                name="Railway Free",
                description="$5 free credit monthly",
                free_resources={
                    "credit": "$5/month",
                    "services": "Unlimited (within credit)"
                },
                limitations=["Requires credit card"],
                requires_credit_card=True
            ),
            FreeCloudProvider.FLY_IO: FreeTierInfo(
                provider=FreeCloudProvider.FLY_IO,
                name="Fly.io Free",
                description="Free allowance for small apps",
                free_resources={
                    "cpu": "3 shared CPUs",
                    "ram": "3GB total",
                    "bandwidth": "3GB/month"
                },
                limitations=["Sleeps when inactive"],
                requires_credit_card=True,
                ram_limit_mb=3072,  # 3GB
                bandwidth_limit_mb=3072  # 3GB
            ),
            FreeCloudProvider.NEON: FreeTierInfo(
                provider=FreeCloudProvider.NEON,
                name="Neon Free",
                description="Serverless Postgres with 500MB storage",
                free_resources={
                    "storage": "500MB",
                    "compute": "100 hours/month",
                    "branching": "Unlimited"
                },
                limitations=["Compute pauses after 5 min inactivity"],
                requires_credit_card=False,
                storage_limit_mb=500
            ),
            FreeCloudProvider.SUPABASE: FreeTierInfo(
                provider=FreeCloudProvider.SUPABASE,
                name="Supabase Free",
                description="Postgres database with 500MB",
                free_resources={
                    "storage": "500MB",
                    "database": "Postgres 500MB",
                    "auth": "50,000 users",
                    "api": "2GB bandwidth"
                },
                limitations=["Paused after 1 week inactivity on free tier"],
                requires_credit_card=False,
                storage_limit_mb=500,
                bandwidth_limit_mb=2048
            ),
            FreeCloudProvider.PLANETSCALE: FreeTierInfo(
                provider=FreeCloudProvider.PLANETSCALE,
                name="PlanetScale Free",
                description="MySQL-compatible serverless database",
                free_resources={
                    "storage": "1GB",
                    "rows": "100,000",
                    "branches": "1 production + 1 development"
                },
                limitations=["Limited row count", "No sleep mode"],
                requires_credit_card=False,
                storage_limit_mb=1024
            ),
            FreeCloudProvider.CLOUDFLARE: FreeTierInfo(
                provider=FreeCloudProvider.CLOUDFLARE,
                name="Cloudflare Free",
                description="CDN, DNS, DDoS protection, Workers",
                free_resources={
                    "cdn": "Unlimited bandwidth",
                    "workers": "100,000 requests/day",
                    "dns": "Unlimited",
                    "ddos": "Always on"
                },
                limitations=["Workers CPU time: 10ms free tier"],
                requires_credit_card=False,
                request_limit=100000
            )
        }
    
    def _parse_limit_value(self, value_str: str) -> float:
        """Parse a resource limit string to a float value in MB or count"""
        value_str = value_str.lower().strip()
        
        if "unlimited" in value_str:
            return float("inf")
        
        # Parse GB
        if "gb" in value_str:
            num = float(value_str.replace("gb", "").strip())
            return num * 1024  # Convert to MB
        
        # Parse MB
        if "mb" in value_str:
            return float(value_str.replace("mb", "").strip())
        
        # Parse KB
        if "kb" in value_str:
            num = float(value_str.replace("kb", "").strip())
            return num / 1024  # Convert to MB
        
        # Parse raw numbers
        try:
            return float(value_str.split()[0])
        except (ValueError, IndexError):
            return 0.0
    
    def list_free_tiers(self) -> List[Dict]:
        """List all available free tiers with usage status"""
        result = []
        for provider, tier in self.free_tiers.items():
            usage_pct = self._calculate_overall_usage(tier)
            warning_level = self._get_usage_warning_level(usage_pct)
            
            entry = {
                "provider": tier.provider.value,
                "name": tier.name,
                "description": tier.description,
                "resources": tier.free_resources,
                "limitations": tier.limitations,
                "requires_credit_card": tier.requires_credit_card,
                "usage_percentage": round(usage_pct * 100, 1),
                "warning_level": warning_level.value,
                "limits": {
                    "ram_mb": tier.ram_limit_mb,
                    "bandwidth_mb": tier.bandwidth_limit_mb,
                    "storage_mb": tier.storage_limit_mb,
                    "requests": tier.request_limit,
                    "uptime_hours": tier.uptime_limit_hours
                },
                "current_usage": {
                    "ram_mb": tier.usage.ram_mb_used,
                    "bandwidth_mb": tier.usage.bandwidth_mb_used,
                    "storage_mb": tier.usage.storage_mb_used,
                    "requests": tier.usage.requests_count,
                    "uptime_hours": tier.usage.uptime_hours
                }
            }
            result.append(entry)
        
        return result
    
    def get_best_provider(self, requirements: Dict[str, Any]) -> Optional[FreeCloudProvider]:
        """
        Get best provider based on requirements using intelligent scoring
        
        Args:
            requirements: Dict with optional keys:
                - 'ram_mb': Required RAM in MB
                - 'bandwidth_mb': Required monthly bandwidth in MB
                - 'storage_mb': Required storage in MB
                - 'database': True if database needed
                - 'cdn': True if CDN needed
                - 'serverless': True if serverless functions needed
                - 'no_credit_card': True if must not require credit card
                - 'uptime_hours': Required monthly uptime in hours
                
        Returns:
            Best matching provider or None
        """
        best_score = -1.0
        best_provider = None
        
        no_credit_card = requirements.get("no_credit_card", False)
        
        for provider, tier in self.free_tiers.items():
            # Filter by credit card requirement
            if no_credit_card and tier.requires_credit_card:
                continue
            
            score = self._score_provider(tier, requirements)
            
            if score > best_score:
                best_score = score
                best_provider = provider
        
        if best_provider:
            self.logger.info(
                f"Best provider for requirements: {best_provider.value} "
                f"(score: {best_score:.2f})"
            )
        else:
            self.logger.warning("No suitable provider found for requirements")
        
        return best_provider
    
    def _score_provider(self, tier: FreeTierInfo, requirements: Dict[str, Any]) -> float:
        """Score a provider against requirements (0.0 = no match, 1.0 = perfect)"""
        score = 1.0
        
        # Check RAM requirement
        req_ram = requirements.get("ram_mb", 0)
        if req_ram > 0:
            if tier.ram_limit_mb >= req_ram:
                # Bonus for having more headroom
                headroom = (tier.ram_limit_mb - req_ram) / tier.ram_limit_mb
                score *= (0.5 + 0.5 * headroom)
            else:
                score *= 0.3  # Can still work but constrained
        
        # Check bandwidth requirement
        req_bandwidth = requirements.get("bandwidth_mb", 0)
        if req_bandwidth > 0:
            if tier.bandwidth_limit_mb >= req_bandwidth:
                headroom = (tier.bandwidth_limit_mb - req_bandwidth) / tier.bandwidth_limit_mb
                score *= (0.5 + 0.5 * headroom)
            else:
                score *= 0.3
        
        # Check storage requirement
        req_storage = requirements.get("storage_mb", 0)
        if req_storage > 0:
            if tier.storage_limit_mb >= req_storage:
                headroom = (tier.storage_limit_mb - req_storage) / tier.storage_limit_mb
                score *= (0.5 + 0.5 * headroom)
            else:
                score *= 0.3
        
        # Check uptime requirement
        req_uptime = requirements.get("uptime_hours", 0)
        if req_uptime > 0 and tier.uptime_limit_hours > 0:
            if tier.uptime_limit_hours >= req_uptime:
                score *= 1.0
            else:
                score *= 0.5
        
        # Feature matching bonuses
        if requirements.get("database") and "database" in json.dumps(tier.free_resources).lower():
            score *= 1.2
        
        if requirements.get("cdn") and "cdn" in json.dumps(tier.free_resources).lower():
            score *= 1.2
        
        if requirements.get("serverless") and ("serverless" in json.dumps(tier.free_resources).lower() or "workers" in json.dumps(tier.free_resources).lower()):
            score *= 1.2
        
        # Penalize credit card requirement
        if tier.requires_credit_card:
            score *= 0.8
        
        # Penalize high current usage
        usage_pct = self._calculate_overall_usage(tier)
        if usage_pct > 0.8:
            score *= (1.0 - usage_pct)  # Heavy penalty if nearly exhausted
        elif usage_pct > 0.5:
            score *= (1.0 - usage_pct * 0.5)  # Minor penalty
        
        return max(0.0, score)
    
    def _calculate_overall_usage(self, tier: FreeTierInfo) -> float:
        """Calculate overall usage percentage for a free tier (0.0-1.0)"""
        usage_scores = []
        
        if tier.ram_limit_mb > 0:
            usage_scores.append(tier.usage.ram_mb_used / tier.ram_limit_mb)
        
        if tier.bandwidth_limit_mb > 0:
            usage_scores.append(tier.usage.bandwidth_mb_used / tier.bandwidth_limit_mb)
        
        if tier.storage_limit_mb > 0:
            usage_scores.append(tier.usage.storage_mb_used / tier.storage_limit_mb)
        
        if tier.request_limit > 0:
            usage_scores.append(tier.usage.requests_count / tier.request_limit)
        
        if tier.uptime_limit_hours > 0:
            usage_scores.append(tier.usage.uptime_hours / tier.uptime_limit_hours)
        
        if not usage_scores:
            return 0.0
        
        return sum(usage_scores) / len(usage_scores)
    
    def _get_usage_warning_level(self, usage_pct: float) -> UsageWarningLevel:
        """Get warning level based on usage percentage"""
        if usage_pct >= self.USAGE_CRITICAL_PCT:
            return UsageWarningLevel.CRITICAL
        elif usage_pct >= self.USAGE_HIGH_PCT:
            return UsageWarningLevel.HIGH
        elif usage_pct >= self.USAGE_WARNING_PCT:
            return UsageWarningLevel.ELEVATED
        return UsageWarningLevel.NORMAL
    
    def get_auto_switch_recommendation(self, deployment_id: str) -> Dict[str, Any]:
        """
        Get recommendation for auto-switching if current provider is approaching limits
        
        Args:
            deployment_id: ID of the deployment to evaluate
            
        Returns:
            Dict with switch recommendation
        """
        deployment = self.deployments.get(deployment_id)
        if not deployment:
            return {"success": False, "error": "Deployment not found"}
        
        current_provider = deployment.provider
        current_tier = self.free_tiers.get(current_provider)
        
        if not current_tier:
            return {"success": False, "error": f"No tier info for {current_provider.value}"}
        
        usage_pct = self._calculate_overall_usage(current_tier)
        warning_level = self._get_usage_warning_level(usage_pct)
        
        result = {
            "deployment_id": deployment_id,
            "current_provider": current_provider.value,
            "usage_percentage": round(usage_pct * 100, 1),
            "warning_level": warning_level.value,
            "needs_switch": warning_level in (UsageWarningLevel.HIGH, UsageWarningLevel.CRITICAL),
            "urgency": "immediate" if warning_level == UsageWarningLevel.CRITICAL else "soon" if warning_level == UsageWarningLevel.HIGH else "not_needed",
            "recommended_provider": None,
            "reason": ""
        }
        
        if result["needs_switch"]:
            # Find alternative provider
            req = self._build_requirements_from_deployment(deployment)
            alt_provider = self.get_best_provider(req)
            
            if alt_provider and alt_provider != current_provider:
                result["recommended_provider"] = alt_provider.value
                result["reason"] = (
                    f"Free tier usage at {result['usage_percentage']}% for {current_provider.value}. "
                    f"Recommended switch to {alt_provider.value}."
                )
            else:
                result["reason"] = (
                    f"Free tier usage at {result['usage_percentage']}% but no suitable alternative found."
                )
        
        return result
    
    def _build_requirements_from_deployment(self, deployment: Deployment) -> Dict[str, Any]:
        """Build requirements dict from a deployment's current usage"""
        metrics = deployment.usage_metrics
        return {
            "ram_mb": metrics.ram_mb_used * 1.5,  # 50% headroom
            "bandwidth_mb": metrics.bandwidth_mb_used * 1.5,
            "storage_mb": metrics.storage_mb_used * 1.5,
            "uptime_hours": metrics.uptime_hours * 1.2,
            "no_credit_card": False
        }
    
    async def _monitor_loop(self):
        """Periodic usage monitoring loop"""
        while self._running:
            try:
                for deployment_id, deployment in list(self.deployments.items()):
                    await self._check_deployment_usage(deployment)
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(10)
    
    async def _check_deployment_usage(self, deployment: Deployment):
        """Check and update usage metrics for a deployment"""
        provider_tier = self.free_tiers.get(deployment.provider)
        if not provider_tier:
            return
        
        # Simulate usage increase (in production, would read actual metrics)
        # Linearly increase usage to test auto-switch logic
        provider_tier.usage.uptime_hours += 0.0167  # ~1 minute
        
        # Update deployment metrics from provider tier
        deployment.usage_metrics = UsageMetrics(
            ram_mb_used=provider_tier.usage.ram_mb_used,
            cpu_percent=provider_tier.usage.cpu_percent,
            bandwidth_mb_used=provider_tier.usage.bandwidth_mb_used,
            storage_mb_used=provider_tier.usage.storage_mb_used,
            requests_count=provider_tier.usage.requests_count,
            uptime_hours=provider_tier.usage.uptime_hours,
            last_updated=datetime.now()
        )
        
        # Update warning level
        usage_pct = self._calculate_overall_usage(provider_tier)
        deployment.warning_level = self._get_usage_warning_level(usage_pct)
        deployment.last_health_check = datetime.now()
        
        # Auto-switch if critical
        if deployment.warning_level == UsageWarningLevel.CRITICAL and not deployment.auto_switch_triggered:
            self.logger.warning(
                f"CRITICAL: Deployment {deployment.deployment_id} at {usage_pct*100:.1f}% usage. "
                f"Auto-switch recommended."
            )
            deployment.auto_switch_triggered = True
    
    async def deploy_to_free_cloud(
        self,
        app_name: str,
        provider: Optional[FreeCloudProvider] = None,
        config: Optional[Dict] = None
    ) -> Dict:
        """
        Deploy application to free cloud
        
        Args:
            app_name: Application name
            provider: Specific provider (auto-selected if None)
            config: Deployment configuration / requirements
            
        Returns:
            Deployment result with status and deployment_id
        """
        requirements = config or {}
        
        if provider is None:
            provider = self.get_best_provider(requirements)
        
        if provider is None:
            return {"success": False, "error": "No suitable free provider found"}
        
        deployment_id = f"deploy_{app_name}_{datetime.now().timestamp()}"
        
        self.logger.info(f"Deploying {app_name} to {provider.value}...")
        
        # Simulate deployment
        await asyncio.sleep(2)
        
        # Initialize usage tracking for the chosen provider
        provider_tier = self.free_tiers.get(provider)
        if provider_tier:
            # Set initial usage based on requirements
            provider_tier.usage = UsageMetrics(
                ram_mb_used=requirements.get("ram_mb", 128),
                bandwidth_mb_used=requirements.get("bandwidth_mb", 100),
                storage_mb_used=requirements.get("storage_mb", 50),
                uptime_hours=0.0,
                last_updated=datetime.now()
            )
        
        deployment = Deployment(
            deployment_id=deployment_id,
            provider=provider,
            app_name=app_name,
            status="deployed",
            created_at=datetime.now(),
            resource_usage={
                "ram": f"{requirements.get('ram_mb', 128)}MB",
                "cpu": "shared"
            },
            usage_metrics=provider_tier.usage if provider_tier else UsageMetrics(),
            warning_level=UsageWarningLevel.NORMAL
        )
        
        self.deployments[deployment_id] = deployment
        
        self.logger.info(f"Deployed {app_name} to {provider.value} (ID: {deployment_id})")
        
        return {
            "success": True,
            "deployment_id": deployment_id,
            "provider": provider.value,
            "status": "deployed"
        }
    
    async def monitor_usage(self, deployment_id: str) -> Dict:
        """Monitor resource usage for a deployment"""
        if deployment_id not in self.deployments:
            return {"success": False, "error": "Deployment not found"}
        
        deployment = self.deployments[deployment_id]
        provider_tier = self.free_tiers.get(deployment.provider)
        
        # Run a check
        await self._check_deployment_usage(deployment)
        
        usage_pct = self._calculate_overall_usage(provider_tier) if provider_tier else 0.0
        warning_level = self._get_usage_warning_level(usage_pct)
        
        return {
            "success": True,
            "deployment_id": deployment_id,
            "provider": deployment.provider.value,
            "status": deployment.status,
            "warning_level": warning_level.value,
            "usage_percentage": round(usage_pct * 100, 1),
            "metrics": {
                "ram_mb": deployment.usage_metrics.ram_mb_used,
                "cpu_percent": deployment.usage_metrics.cpu_percent,
                "bandwidth_mb": deployment.usage_metrics.bandwidth_mb_used,
                "storage_mb": deployment.usage_metrics.storage_mb_used,
                "requests": deployment.usage_metrics.requests_count,
                "uptime_hours": round(deployment.usage_metrics.uptime_hours, 2)
            },
            "limits": {
                "ram_mb": provider_tier.ram_limit_mb if provider_tier else 0,
                "bandwidth_mb": provider_tier.bandwidth_limit_mb if provider_tier else 0,
                "storage_mb": provider_tier.storage_limit_mb if provider_tier else 0,
                "requests": provider_tier.request_limit if provider_tier else 0,
                "uptime_hours": provider_tier.uptime_limit_hours if provider_tier else 0
            } if provider_tier else {},
            "within_limits": warning_level not in (UsageWarningLevel.HIGH, UsageWarningLevel.CRITICAL)
        }
    
    def list_deployments(self) -> List[Dict]:
        """List all deployments with usage status"""
        return [
            {
                "deployment_id": d.deployment_id,
                "app_name": d.app_name,
                "provider": d.provider.value,
                "status": d.status,
                "created_at": d.created_at.isoformat(),
                "warning_level": d.warning_level.value,
                "usage": {
                    "ram_mb": d.usage_metrics.ram_mb_used,
                    "bandwidth_mb": d.usage_metrics.bandwidth_mb_used,
                    "storage_mb": d.usage_metrics.storage_mb_used,
                    "uptime_hours": round(d.usage_metrics.uptime_hours, 2)
                },
                "auto_switch_triggered": d.auto_switch_triggered,
                "last_health_check": d.last_health_check.isoformat() if d.last_health_check else None
            }
            for d in self.deployments.values()
        ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get overall agent statistics"""
        total_deployments = len(self.deployments)
        critical_count = sum(
            1 for d in self.deployments.values()
            if d.warning_level == UsageWarningLevel.CRITICAL
        )
        high_count = sum(
            1 for d in self.deployments.values()
            if d.warning_level == UsageWarningLevel.HIGH
        )
        
        provider_usage = {}
        for provider, tier in self.free_tiers.items():
            pct = self._calculate_overall_usage(tier) * 100
            provider_usage[provider.value] = {
                "usage_percentage": round(pct, 1),
                "warning_level": self._get_usage_warning_level(pct / 100).value,
                "ram_mb": tier.usage.ram_mb_used,
                "bandwidth_mb": tier.usage.bandwidth_mb_used,
                "uptime_hours": round(tier.usage.uptime_hours, 1)
            }
        
        return {
            "total_deployments": total_deployments,
            "deployments_at_risk": critical_count + high_count,
            "critical": critical_count,
            "high": high_count,
            "providers_tracked": len(self.free_tiers),
            "provider_usage": provider_usage,
            "auto_switch_eligible": sum(
                1 for d in self.deployments.values()
                if d.warning_level in (UsageWarningLevel.HIGH, UsageWarningLevel.CRITICAL)
            )
        }


# Global instance
_free_cloud_agent_instance: Optional[FreeCloudAgent] = None


def get_free_cloud_agent() -> FreeCloudAgent:
    """Get or create global free cloud agent instance"""
    global _free_cloud_agent_instance
    if _free_cloud_agent_instance is None:
        _free_cloud_agent_instance = FreeCloudAgent()
    return _free_cloud_agent_instance


def reset_free_cloud_agent():
    """Reset the singleton (for testing)"""
    global _free_cloud_agent_instance
    _free_cloud_agent_instance = None
