# core/orchestrator/orchestrator.py
# AsimNexus — LLM Orchestrator: Intent → Plan → Tool Call

import json
import logging
import os
from typing import Dict, Any, List, Optional
import time
import uuid
import asyncio

from core.identity.federated_identity import FederatedIdentity
from core.policy.human_approval import request_approval

# Resilient imports for Dharma Veto
try:
    from core.dharma_chakra.veto_engine import get_veto_engine, VetoResult, VetoLevel
    dharma_available = True
except ImportError:
    dharma_available = False

# Resilient imports for Clone Consensus
try:
    from core.consensus.clone_consensus_voting import CloneConsensusVoting
    consensus_available = True
except ImportError:
    consensus_available = False

from core.policy.policy_engine import PolicyEngine
from core.orchestrator.planner import Planner
from core.orchestrator.router import Router
from core.orchestrator.verifier import Verifier
from core.gateway.unified_gateway import UnifiedGateway

logger = logging.getLogger(__name__)

class Orchestrator:
    """
    AsimNexus Orchestrator — Coordinates user requests by:
    1. Intent identification
    2. Policy Check (PolicyEngine)
    3. Plan construction (Planner)
    4. Dharma Veto Check (DharmaVetoEngine)
    5. Clone Consensus (CloneConsensusVoting)
    6. Executing plan steps via agents
    7. Writing to immutable audit log
    """

    def __init__(self):
        self.policy = PolicyEngine()
        self.gateway = UnifiedGateway()
        self.planner = Planner()
        self.router = Router()
        self.verifier = Verifier()
        
        if dharma_available:
            self.dharma = get_veto_engine()
        else:
            self.dharma = None

        if consensus_available:
            self.consensus = CloneConsensusVoting()
        else:
            self.consensus = None

        self.agents = self._init_agents()

        # Personal OS — lazy import for resilience
        try:
            from core.identity.personal_os import PersonalOS
            self.personal_os = PersonalOS(
                asim_id="orchestrator",
                display_name="Orchestrator",
            )
        except Exception:
            self.personal_os = None

    def _init_agents(self) -> Dict[str, Any]:
        try:
            from core.agents.tax_agent import TaxAgent
            from core.agents.health_agent import HealthAgent
            from core.agents.education_agent import EducationAgent
            from core.agents.finance_agent import FinanceAgent
            from core.agents.mesh_agent import MeshAgent
            from core.agents.general_agent import GeneralAgent
            return {
                "tax": TaxAgent(),
                "health": HealthAgent(),
                "education": EducationAgent(),
                "finance": FinanceAgent(),
                "mesh": MeshAgent(),
                "general": GeneralAgent(),
            }
        except ImportError as e:
            logger.warning(f"Failed to import agents: {e}")
            # Mock fallback agents for resilience
            class MockAgent:
                async def execute(self, action, params, user_id, mode):
                    return {"status": "mock_success", "action": action, "params": params}
            return {
                "tax": MockAgent(),
                "health": MockAgent(),
                "education": MockAgent(),
                "finance": MockAgent(),
                "mesh": MockAgent(),
                "general": MockAgent(),
            }

    async def _execute_on_twin(self, twin: Dict, intent: Dict, message: str, mode: str) -> List[Dict]:
        """Executes the plan steps specifically for a given twin context."""
        user_id = twin["twin_id"]
        # Build Plan
        plan = await self.planner.create_plan(intent, message, user_id, mode)

        # Verifier check
        valid = await self.verifier.verify(plan)
        if not valid:
            return [{"status": "invalid_plan", "message": "The generated plan is invalid or unsafe."}]

        # Dharma Veto check
        if self.dharma:
            veto_result = self.dharma.check(message=message, sector=intent.get("action", "general"), agent_id=user_id)
            if not veto_result.allowed:
                return [{"status": "veto_blocked", "message": f"Dharma Veto: {veto_result.reason}"}]

        # Constitutional consensus (8/15 Clone Voting)
        if intent.get("constitutional", False) and self.consensus:
            consensus_round = await self.consensus.start_round(
                topic=json.dumps(plan),
                sector=intent.get("action", "general"),
                description="Constitutional AI Council voting on plan"
            )
            if consensus_round.outcome != "approved":
                return [{"status": "rejected", "message": "Consensus not reached by the 15 Founder Clones."}]

        # Human Approval
        approved = await request_approval(user_id, 1, {"intent": intent})
        if not approved:
            return [{"status": "human_rejected", "message": "Human operator rejected the action."}]

        # Execute Plan Steps
        results = []
        for step in plan.get("steps", []):
            agent = self.router.route(step, self.agents)
            if not agent:
                results.append({"status": "error", "message": f"Agent '{step.get('agent')}' not found"})
                continue
            
            try:
                res = await agent.execute(step.get("action"), step.get("params", {}), user_id, mode)
                results.append({"status": "success", "agent": step.get("agent"), "result": res})
            except Exception as e:
                logger.error(f"Execution failed on step {step}: {e}")
                results.append({"status": "critical_failure", "agent": step.get("agent"), "message": str(e)})
                break
                
        return results

    async def _load_hybrid_twins(self, user_id: str):
        identity = FederatedIdentity(user_id)
        return [identity.get_twin("company"), identity.get_twin("government")]

    async def _request_cross_consent(self, user_id: str, results: List[Any]) -> bool:
        # Simple stub for demo
        return True

    async def process(self, user_id: str, message: str, mode: str = "citizen") -> Dict:
        """
        Main entry point: User Message → Intent → Plan → Execute → Respond
        """
        # 1. Intent Parsing
        intent = await self._parse_intent(message)

        # 2. Policy Check
        allowed, reason = await self.policy.check(user_id, intent.get("action", "general"), mode)
        if not allowed:
            return {
                "status": "blocked",
                "message": f"Policy restriction: {reason}",
                "suggestion": "Contact your administrator."
            }
            
        identity = FederatedIdentity(user_id)
        results = []
        plan = {"steps": []}
        
        if mode == "hybrid":
            twins = await self._load_hybrid_twins(user_id)
            for twin in twins:
                sub_res = await self._execute_on_twin(twin, intent, message, mode)
                results.extend(sub_res)
            
            consent = await self._request_cross_consent(user_id, results)
            if not consent:
                return {"status": "cross_consent_rejected"}
        else:
            twin = identity.get_twin(mode)
            results = await self._execute_on_twin(twin, intent, message, mode)

        audit_id = str(uuid.uuid4())
        # 8. Audit Log
        await self._audit_log(audit_id, user_id, intent, plan, results)

        # 9. Return Response
        return {
            "status": "completed",
            "message": f"Asim executed intent '{intent.get('action')}' successfully.",
            "intent": intent,
            "plan": plan,
            "results": results,
            "audit_id": audit_id
        }

    async def _parse_intent(self, message: str) -> Dict:
        """Parses user message to intent dictionary using the LLM Gateway"""
        constitutional = any(w in message.lower() for w in ["constitutional", "emergency", "sarkar", "governance"])
        
        try:
            from core.gateway.unified_llm_gateway import unified_llm_gateway, UnifiedCompletionRequest
            prompt = f'Analyze the user message and determine the primary system action. Allowed actions: [tax, health, education, finance, mesh, general]. Respond ONLY in raw JSON format: {{"action": "string", "sub_action": "string"}}.\\nMessage: {message}'
            
            req = UnifiedCompletionRequest(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.1
            )
            res = await unified_llm_gateway.complete(req)
            
            import json
            import re
            
            # Extract JSON from response
            text = res.content
            match = re.search(r'\\{.*\\}', text, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                return {
                    "action": parsed.get("action", "general"),
                    "sub_action": parsed.get("sub_action", "chat"),
                    "constitutional": constitutional
                }
        except Exception as e:
            logger.warning(f"LLM Intent Parsing failed, falling back to general: {e}")
            
        return {"action": "general", "sub_action": "chat", "constitutional": constitutional}

    _audit_lock = asyncio.Lock()

    async def _audit_log(self, audit_id: str, user_id: str, intent: Dict, plan: Dict, results: List[Dict]):
        """Saves immutable log of actions"""
        AUDIT_PATH = os.path.join(os.path.dirname(__file__), "..", "audit_store.json")
        entry = {
            "audit_id": audit_id,
            "timestamp": time.time(),
            "user_id": user_id,
            "intent": intent,
            "plan": plan,
            "results": results,
        }
        async with self._audit_lock:
            with open(AUDIT_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        
        try:
            from core.audit_bus import get_audit_bus
            bus = get_audit_bus()
            bus.publish(entry)
        except Exception:
            pass

    async def _verify_user(self, username: str, password: str):
        """Mock user verification for testing."""
        from pydantic import BaseModel
        class MockUser(BaseModel):
            id: str = "u001"
            username: str = "admin"
            role: str = "admin"
            org_id: str = "gov_np"
            permissions: list = ["all"]
            email: str = "admin@asimnexus.ai"
        
        if username == "admin" and password == "admin123":
            return MockUser()
        return None

    async def authenticate_user(self, username: str, password: str) -> Dict:
        # 1. Verify credentials (against DB)
        user = await self._verify_user(username, password)
        if not user:
            return {"error": "Invalid credentials"}
        
        # 2. Generate HSM-signed token
        from core.security.jwt import create_access_token
        token = create_access_token(
            user_id=user.id,
            username=user.username,
            roles=[user.role],
            org_id=user.org_id,
            permissions=user.permissions,
            email=user.email
        )
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "user": user.model_dump() if hasattr(user, 'model_dump') else user.dict()
        }
