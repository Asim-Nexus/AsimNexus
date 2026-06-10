#!/usr/bin/env python3
"""
STATUS: REAL — Override Integrator
===================================
Bridges Human Override Engine with Veto Engine and Policy Gate.

Provides opt-in integration functions that wrap existing check() methods
with automatic override request creation when human intervention is required.

Design:
- Does NOT modify existing VetoEngine or PolicyGate code
- Provides wrapper functions that add override creation on top of existing checks
- Returns (original_result, override_request_id) tuples
- override_request_id is None if no override was needed
- Uses singleton factories for HumanOverrideEngine

Integration Points:
1. Veto Engine check() → REQUIRES_HUMAN → override request (CONSTITUTIONAL trigger)
2. Policy Gate evaluate_action() → CRITICAL → override request (POLICY_CRITICAL trigger)
3. Policy Gate request_approval() → auto-creates override for CRITICAL risk
"""

import hashlib
import logging
from typing import Any, Dict, List, Optional, Tuple

from core.dharma_chakra.veto_engine import DharmaVetoEngine, VetoResult
from core.human_override_engine import (
    HumanOverrideEngine,
    OverrideTier,
    OverrideTrigger,
    get_human_override_engine,
)
from core.policy_gate import ActionCategory, ActionRisk, ActionRequest, PolicyGate

logger = logging.getLogger("OverrideIntegrator")


# =============================================================================
# Veto Engine Integration
# =============================================================================

def veto_check_with_override(
    engine: DharmaVetoEngine,
    message: str,
    sector: str = "general",
    agent_id: str = "user",
    context: Optional[Dict[str, Any]] = None,
    override_engine: Optional[HumanOverrideEngine] = None,
    escalation_tier: OverrideTier = OverrideTier.PERSONAL,
) -> Tuple[VetoResult, Optional[str]]:
    """Run veto check and auto-create override request if human required.

    This wraps DharmaVetoEngine.check() with Human Override Engine integration.
    When the veto engine determines that human confirmation is required,
    an override request is automatically created with CONSTITUTIONAL trigger.

    Args:
        engine: DharmaVetoEngine instance
        message: The action message being checked
        sector: Action sector (general, finance, emergency, etc.)
        agent_id: The agent/user performing the action
        context: Additional context for the veto check
        override_engine: Optional HumanOverrideEngine instance (uses singleton if None)
        escalation_tier: Initial override tier (default PERSONAL)

    Returns:
        Tuple of (VetoResult, override_request_id_or_None)
    """
    # Run the standard veto check first
    result = engine.check(
        message=message,
        sector=sector,
        agent_id=agent_id,
        context=context,
    )

    # If human confirmation is required, create an override request
    if result.requires_human:
        override_id = _create_veto_override(
            result=result,
            message=message,
            agent_id=agent_id,
            sector=sector,
            context=context or {},
            override_engine=override_engine,
            escalation_tier=escalation_tier,
        )
        return result, override_id

    return result, None


def _create_veto_override(
    result: VetoResult,
    message: str,
    agent_id: str,
    sector: str,
    context: Dict[str, Any],
    override_engine: Optional[HumanOverrideEngine],
    escalation_tier: OverrideTier,
) -> str:
    """Create an override request for a veto-triggered human confirmation."""
    hoe = override_engine or get_human_override_engine()

    # Use full SHA-256 for the action hash
    action_hash = hashlib.sha256(message.encode()).hexdigest()

    # Build a human-readable action preview
    preview = message[:200]
    if len(message) > 200:
        preview += "…"

    # Determine appropriate tier based on sector sensitivity
    tier = escalation_tier
    sensitive_sectors = {"emergency", "legal", "government", "defense", "finance"}
    if sector in sensitive_sectors and tier == OverrideTier.PERSONAL:
        tier = OverrideTier.TRUSTED_CIRCLE

    request_id = hoe.request_override(
        action_hash=action_hash,
        action_preview=preview,
        trigger=OverrideTrigger.CONSTITUTIONAL,
        tier=tier,
        requested_by=agent_id,
        metadata={
            "veto_rule": result.rule_triggered,
            "veto_reason": result.reason,
            "veto_level": result.level.value,
            "sector": sector,
            "source": "dharma_veto_engine",
        },
    )

    logger.info(
        f"🔗 Veto override created: {request_id} "
        f"(rule={result.rule_triggered}, sector={sector}, tier={tier.value})"
    )
    return request_id


# =============================================================================
# Policy Gate Integration
# =============================================================================

def policy_evaluate_with_override(
    policy_gate: PolicyGate,
    action_type: str,
    category: ActionCategory,
    user_id: str = "system",
    parameters: Optional[Dict[str, Any]] = None,
    override_engine: Optional[HumanOverrideEngine] = None,
) -> Tuple[Dict[str, Any], Optional[str]]:
    """Evaluate a policy action and auto-create override request if CRITICAL.

    This wraps PolicyGate.evaluate_action() with Human Override Engine integration.
    When the risk level is CRITICAL, an override request is automatically created
    with POLICY_CRITICAL trigger.

    Args:
        policy_gate: PolicyGate instance
        action_type: Type of action being evaluated
        category: Action category
        user_id: The user performing the action
        parameters: Action parameters
        override_engine: Optional HumanOverrideEngine instance (uses singleton if None)

    Returns:
        Tuple of (evaluation_result, override_request_id_or_None)
    """
    # Evaluate the action
    result = policy_gate.evaluate_action(
        action_type=action_type,
        category=category,
        parameters=parameters or {},
    )

    # If risk is CRITICAL, create an override request
    if result.risk_level.value == "critical":
        override_id = _create_policy_override(
            action_type=action_type,
            category=category,
            user_id=user_id,
            parameters=parameters or {},
            evaluation_result=result,
            override_engine=override_engine,
        )
        return result, override_id

    return result, None


def _create_policy_override(
    action_type: str,
    category: ActionCategory,
    user_id: str,
    parameters: Dict[str, Any],
    evaluation_result: Dict[str, Any],
    override_engine: Optional[HumanOverrideEngine],
) -> str:
    """Create an override request for a policy-critical action."""
    hoe = override_engine or get_human_override_engine()

    # Create a deterministic action hash
    action_str = f"{action_type}:{category.value}:{parameters}"
    action_hash = hashlib.sha256(action_str.encode()).hexdigest()

    # Build action preview
    preview = f"{category.value} :: {action_type}"
    params_str = str(parameters)
    if params_str:
        preview += f" ({params_str[:150]})"
    if len(preview) > 200:
        preview = preview[:200] + "…"

    request_id = hoe.request_override(
        action_hash=action_hash,
        action_preview=preview,
        trigger=OverrideTrigger.POLICY_CRITICAL,
        tier=OverrideTier.PERSONAL,
        requested_by=user_id,
        metadata={
            "policy_action_type": action_type,
            "policy_category": category.value,
            "policy_risk_level": "critical",
            "source": "policy_gate",
        },
    )

    logger.info(
        f"🔗 Policy override created: {request_id} "
        f"(action={action_type}, category={category.value})"
    )
    return request_id


def policy_approve_with_override(
    policy_gate: PolicyGate,
    action_type: str,
    category: ActionCategory,
    user_id: str = "system",
    parameters: Optional[Dict[str, Any]] = None,
    override_engine: Optional[HumanOverrideEngine] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Request policy approval and create override request for CRITICAL actions.

    Combines evaluate_action() → request_approval() → override creation
    in one call for CRITICAL risk actions.

    Args:
        policy_gate: PolicyGate instance
        action_type: Type of action
        category: Action category
        user_id: The user requesting
        parameters: Action parameters
        override_engine: Optional HumanOverrideEngine

    Returns:
        Tuple of (approval_request_id_or_None, override_request_id_or_None)
    """
    evaluation, override_id = policy_evaluate_with_override(
        policy_gate=policy_gate,
        action_type=action_type,
        category=category,
        user_id=user_id,
        parameters=parameters,
        override_engine=override_engine,
    )

    # If evaluation says it's safe, no approval needed
    if evaluation.risk_level.value in ("low", "safe") and evaluation.approved:
        return None, override_id

    # Request approval through policy gate
    approval_id = policy_gate.request_approval(
        action_type=action_type,
        category=category,
        user_id=user_id,
        parameters=parameters or {},
    )

    return approval_id, override_id


# =============================================================================
# Convenience Wrappers
# =============================================================================

def approve_with_override(
    request_id: str,
    human_id: str,
    reason: str = "",
    override_engine: Optional[HumanOverrideEngine] = None,
) -> Dict[str, Any]:
    """Approve a pending override request.

    Wraps HumanOverrideEngine.confirm_override() for use by API endpoints.

    Args:
        request_id: The override request ID
        human_id: Identifier of the human approving
        reason: Human's reason for approval
        override_engine: Optional engine instance (uses singleton if None)

    Returns:
        Result dict from the engine
    """
    hoe = override_engine or get_human_override_engine()
    return hoe.confirm_override(
        request_id=request_id,
        human_id=human_id,
        reason=reason,
    )


def reject_with_override(
    request_id: str,
    human_id: str,
    reason: str = "",
    override_engine: Optional[HumanOverrideEngine] = None,
) -> Dict[str, Any]:
    """Reject a pending override request.

    Wraps HumanOverrideEngine.reject_override() for use by API endpoints.

    Args:
        request_id: The override request ID
        human_id: Identifier of the human rejecting
        reason: Why the override was rejected
        override_engine: Optional engine instance (uses singleton if None)

    Returns:
        Result dict from the engine
    """
    hoe = override_engine or get_human_override_engine()
    return hoe.reject_override(
        request_id=request_id,
        human_id=human_id,
        reason=reason,
    )


def escalate_with_override(
    request_id: str,
    human_id: str,
    reason: str = "",
    override_engine: Optional[HumanOverrideEngine] = None,
) -> Dict[str, Any]:
    """Reject an override and escalate to the next tier.

    This is equivalent to a rejection with automatic escalation.
    Wraps HumanOverrideEngine.reject_override() which handles the
    escalation chain automatically for CONSTITUTIONAL and POLICY_CRITICAL triggers.

    Args:
        request_id: The override request ID
        human_id: Identifier of the human escalating
        reason: Why the override is being escalated
        override_engine: Optional engine instance (uses singleton if None)

    Returns:
        Result dict from the engine (may include escalated_to info)
    """
    hoe = override_engine or get_human_override_engine()
    return hoe.reject_override(
        request_id=request_id,
        human_id=human_id,
        reason=reason,
    )


def list_pending_overrides(
    override_engine: Optional[HumanOverrideEngine] = None,
) -> List[Dict[str, Any]]:
    """List all pending override requests.

    Args:
        override_engine: Optional engine instance (uses singleton if None)

    Returns:
        List of pending override request dicts
    """
    hoe = override_engine or get_human_override_engine()
    return hoe.list_pending()


__all__ = [
    "veto_check_with_override",
    "policy_evaluate_with_override",
    "policy_approve_with_override",
    "approve_with_override",
    "reject_with_override",
    "escalate_with_override",
    "list_pending_overrides",
]
