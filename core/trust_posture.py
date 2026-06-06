#!/usr/bin/env python3
"""
STATUS: REAL — Trust posture assessment scoring engine
ASIMNEXUS Trust Posture Engine
==============================
Computes dynamic security trust levels from device state, authentication freshness,
operational mode, target privacy ratings, and policy rule history.
"""

from typing import Dict, Any

def posture_level(score: float) -> str:
    """Map numeric score (0.0 - 1.0) to dynamic trust levels."""
    if score >= 0.90:
        return "trusted"
    elif score >= 0.75:
        return "high"
    elif score >= 0.50:
        return "medium"
    elif score >= 0.25:
        return "low"
    else:
        return "untrusted"


def assess_posture(*, device_trust: str, session_age_sec: int, mode: str, privacy_level: str, policy_score: float) -> Dict[str, Any]:
    """
    Assess posture dynamically based on multiple security factors.
    Returns dictionary with numeric score, assigned level, and factor breakdown.
    """
    # 1. Device Trust Score
    dev_map = {"trusted": 1.0, "verified": 0.8, "unknown": 0.4, "compromised": 0.0}
    dev_score = dev_map.get(device_trust.lower(), 0.3)

    # 2. Session Freshness
    if session_age_sec < 900:
        session_score = 1.0
    elif session_age_sec < 3600:
        session_score = 0.85
    elif session_age_sec < 86400:
        session_score = 0.6
    else:
        session_score = 0.2

    # 3. Policy & Denial History
    pol_score = max(0.0, min(1.0, policy_score))

    # Calculate weighted average
    overall_score = (dev_score * 0.4) + (session_score * 0.3) + (pol_score * 0.3)

    # Modifiers:
    # Highly sensitive data under "government" or "company" modes raises risk context;
    # if device trust is low, downgrade overall score significantly.
    if privacy_level == "highly_sensitive" and device_trust != "trusted":
        overall_score *= 0.6
    
    if mode in ["government", "company"] and session_score < 0.6:
        overall_score *= 0.8

    level = posture_level(overall_score)

    return {
        "score": round(overall_score, 3),
        "level": level,
        "metrics": {
            "device_score": dev_score,
            "session_score": session_score,
            "policy_score": pol_score
        },
        "inputs": {
            "device_trust": device_trust,
            "session_age_sec": session_age_sec,
            "mode": mode,
            "privacy_level": privacy_level
        }
    }


def posture_reason(data: Dict[str, Any]) -> str:
    """Generate human-readable summary explaining the trust posture assessment."""
    level = data["level"]
    score = data["score"]
    inputs = data["inputs"]
    metrics = data["metrics"]

    reason_parts = [f"Trust posture is '{level.upper()}' (score: {score})."]

    if metrics["device_score"] < 0.5:
        reason_parts.append(f"Device trust is untrusted/unknown ({inputs['device_trust']}).")
    if metrics["session_score"] < 0.5:
        reason_parts.append("Session is stale (requires re-auth verification).")
    if metrics["policy_score"] < 0.7:
        reason_parts.append("Recent security policy triggers or blocks detected.")
    
    if len(reason_parts) == 1:
        reason_parts.append("All security attributes meet or exceed baseline criteria.")

    return " ".join(reason_parts)
