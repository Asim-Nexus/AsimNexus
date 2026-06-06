#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade trust posture assessment tests
ASIMNEXUS Trust Posture Tests
==============================
Tests for assess_posture, posture_level, and posture_reason.
"""

import pytest
from core.trust_posture import posture_level, assess_posture, posture_reason


class TestPostureLevel:
    """Tests for the posture_level score-to-label mapping."""

    def test_trusted_at_090(self):
        assert posture_level(0.90) == "trusted"

    def test_trusted_above_090(self):
        assert posture_level(1.0) == "trusted"

    def test_high_at_075(self):
        assert posture_level(0.75) == "high"

    def test_high_between_075_and_090(self):
        assert posture_level(0.80) == "high"

    def test_medium_at_050(self):
        assert posture_level(0.50) == "medium"

    def test_medium_between_050_and_075(self):
        assert posture_level(0.60) == "medium"

    def test_low_at_025(self):
        assert posture_level(0.25) == "low"

    def test_low_between_025_and_050(self):
        assert posture_level(0.30) == "low"

    def test_untrusted_below_025(self):
        assert posture_level(0.0) == "untrusted"

    def test_untrusted_at_024(self):
        assert posture_level(0.24) == "untrusted"


class TestAssessPosture:
    """Tests for the assess_posture function."""

    def test_trusted_device_full_trust(self):
        """Trusted device with fresh session gives 'trusted' posture."""
        result = assess_posture(
            device_trust="trusted",
            session_age_sec=60,
            mode="personal",
            privacy_level="public",
            policy_score=1.0,
        )
        assert result["level"] == "trusted"
        assert result["score"] >= 0.90

    def test_verified_device_high_posture(self):
        """Verified device with fresh session gives 'high' posture."""
        result = assess_posture(
            device_trust="verified",
            session_age_sec=60,
            mode="personal",
            privacy_level="public",
            policy_score=1.0,
        )
        assert result["level"] in ("trusted", "high")
        assert result["score"] >= 0.75

    def test_unknown_device_lower_score(self):
        """Unknown device produces lower score."""
        result = assess_posture(
            device_trust="unknown",
            session_age_sec=60,
            mode="personal",
            privacy_level="public",
            policy_score=1.0,
        )
        assert result["score"] < 0.90

    def test_compromised_device_minimal_trust(self):
        """Compromised device produces very low score."""
        result = assess_posture(
            device_trust="compromised",
            session_age_sec=60,
            mode="personal",
            privacy_level="public",
            policy_score=1.0,
        )
        # compromised -> dev_score=0.0, session=1.0, policy=1.0 => 0.6
        assert result["score"] < 0.70

    def test_stale_session_reduces_score(self):
        """Old session reduces trust score."""
        fresh = assess_posture(
            device_trust="trusted",
            session_age_sec=60,
            mode="personal",
            privacy_level="public",
            policy_score=1.0,
        )
        stale = assess_posture(
            device_trust="trusted",
            session_age_sec=90000,  # > 24h
            mode="personal",
            privacy_level="public",
            policy_score=1.0,
        )
        assert stale["score"] < fresh["score"]

    def test_low_policy_score_reduces_trust(self):
        """Low policy score reduces overall trust."""
        good = assess_posture(
            device_trust="trusted",
            session_age_sec=60,
            mode="personal",
            privacy_level="public",
            policy_score=1.0,
        )
        bad = assess_posture(
            device_trust="trusted",
            session_age_sec=60,
            mode="personal",
            privacy_level="public",
            policy_score=0.0,
        )
        assert bad["score"] < good["score"]

    def test_highly_sensitive_with_untrusted_device_downgrade(self):
        """Highly sensitive data + non-trusted device applies 0.6 multiplier."""
        result = assess_posture(
            device_trust="unknown",
            session_age_sec=60,
            mode="personal",
            privacy_level="highly_sensitive",
            policy_score=1.0,
        )
        # Score should be significantly reduced
        assert result["score"] < 0.60

    def test_government_mode_stale_session_downgrade(self):
        """Government mode + stale session applies 0.8 multiplier."""
        result = assess_posture(
            device_trust="trusted",
            session_age_sec=3600,  # 1 hour, session_score=0.85
            mode="government",
            privacy_level="public",
            policy_score=1.0,
        )
        # Should still be trusted but score reflects mode modifier
        assert result["level"] in ("trusted", "high")

    def test_company_mode_stale_session_downgrade(self):
        """Company mode + session score < 0.6 applies multiplier."""
        result = assess_posture(
            device_trust="trusted",
            session_age_sec=90000,  # > 24h, session_score=0.2
            mode="company",
            privacy_level="public",
            policy_score=1.0,
        )
        assert result["score"] < 0.70

    def test_assess_posture_returns_all_keys(self):
        """assess_posture returns dict with all expected keys."""
        result = assess_posture(
            device_trust="trusted",
            session_age_sec=60,
            mode="personal",
            privacy_level="public",
            policy_score=1.0,
        )
        assert "score" in result
        assert "level" in result
        assert "metrics" in result
        assert "inputs" in result
        assert "device_score" in result["metrics"]
        assert "session_score" in result["metrics"]
        assert "policy_score" in result["metrics"]

    def test_assess_posture_inputs_recorded(self):
        """assess_posture records all input parameters."""
        result = assess_posture(
            device_trust="verified",
            session_age_sec=500,
            mode="family",
            privacy_level="private",
            policy_score=0.85,
        )
        assert result["inputs"]["device_trust"] == "verified"
        assert result["inputs"]["session_age_sec"] == 500
        assert result["inputs"]["mode"] == "family"
        assert result["inputs"]["privacy_level"] == "private"


class TestPostureReason:
    """Tests for the posture_reason function."""

    def test_posture_reason_trusted(self):
        """posture_reason generates message for trusted posture."""
        data = {
            "level": "trusted",
            "score": 0.95,
            "metrics": {"device_score": 1.0, "session_score": 1.0, "policy_score": 1.0},
            "inputs": {"device_trust": "trusted", "session_age_sec": 60, "mode": "personal", "privacy_level": "public"},
        }
        reason = posture_reason(data)
        assert "TRUSTED" in reason
        assert "baseline criteria" in reason

    def test_posture_reason_low_device_trust(self):
        """posture_reason mentions low device trust."""
        data = {
            "level": "low",
            "score": 0.35,
            "metrics": {"device_score": 0.0, "session_score": 1.0, "policy_score": 1.0},
            "inputs": {"device_trust": "compromised", "session_age_sec": 60, "mode": "personal", "privacy_level": "public"},
        }
        reason = posture_reason(data)
        assert "compromised" in reason

    def test_posture_reason_stale_session(self):
        """posture_reason mentions stale session."""
        data = {
            "level": "medium",
            "score": 0.55,
            "metrics": {"device_score": 1.0, "session_score": 0.2, "policy_score": 1.0},
            "inputs": {"device_trust": "trusted", "session_age_sec": 90000, "mode": "personal", "privacy_level": "public"},
        }
        reason = posture_reason(data)
        assert "stale" in reason or "re-auth" in reason

    def test_posture_reason_policy_issues(self):
        """posture_reason mentions policy triggers."""
        data = {
            "level": "medium",
            "score": 0.55,
            "metrics": {"device_score": 1.0, "session_score": 1.0, "policy_score": 0.3},
            "inputs": {"device_trust": "trusted", "session_age_sec": 60, "mode": "personal", "privacy_level": "public"},
        }
        reason = posture_reason(data)
        assert "policy" in reason or "block" in reason

    def test_posture_reason_returns_string(self):
        """posture_reason always returns a non-empty string."""
        data = {
            "level": "trusted",
            "score": 1.0,
            "metrics": {"device_score": 1.0, "session_score": 1.0, "policy_score": 1.0},
            "inputs": {"device_trust": "trusted", "session_age_sec": 60, "mode": "personal", "privacy_level": "public"},
        }
        reason = posture_reason(data)
        assert isinstance(reason, str)
        assert len(reason) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
