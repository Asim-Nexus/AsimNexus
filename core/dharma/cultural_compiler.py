from __future__ import annotations

"""
STATUS: CONCEPT — Auto-labeled by batch_label.py
"""

"""
core/dharma/cultural_compiler.py
AsimNexus — Cultural Sovereignty Compiler
==========================================
Filters ALL incoming "global standards", protocols, or actions
through local cultural and legal context.

Core function:
  "Universal Standards imposed from outside are NOT automatically accepted.
   They are passed through this compiler first. Local community decides."

Checks:
  1. Sovereignty Invasive — data drain, foreign control, resource extraction
  2. Cultural Anomaly     — conflicts with local norms, language, values
  3. Legal Compliance     — checks against local legal rules (Nepal default)
  4. Language Sovereignty — detects imposed language/script replacement
  5. Economic Extraction  — detects debt-leverage, ESG coercion patterns

"प्रविधि मानिसको दास हो, मालिक होइन।"
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("AsimNexus.CulturalCompiler")


# ─── LOCAL CONTEXT PROFILES ───────────────────────────────────────────────────
# Each profile defines what sovereignty means for a community.
# Default: Nepal (can be extended to any community)

LOCAL_PROFILES: Dict[str, Dict[str, Any]] = {
    "nepal": {
        "language":          ["nepali", "ne", "nepal"],
        "official_lang":     "Nepali",
        "script":            "Devanagari",
        "legal_system":      "Constitutional Democracy",
        "sovereignty_keys":  ["nepal", "nepali", "dharma", "sambidhan"],
        "sensitive_topics":  ["federalism", "religion", "caste", "land"],
        "external_risk_orgs": ["imf", "world bank", "blackrock", "vanguard",
                                "state street", "esg rating", "wef"],
        "local_values":       ["community", "family", "nature", "dharma",
                               "local economy", "panchayat", "guthi"],
    },
    "global": {
        "language":          ["english", "en"],
        "official_lang":     "English",
        "script":            "Latin",
        "legal_system":      "International",
        "sovereignty_keys":  [],
        "sensitive_topics":  [],
        "external_risk_orgs": ["blackrock", "vanguard", "state street",
                                "esg rating agency"],
        "local_values":       [],
    },
}

# Sovereignty-invasive patterns (hard blocks)
SOVEREIGNTY_INVASIVE = [
    "mandatory data sharing",
    "required compliance to global standard",
    "esg score requirement",
    "external audit mandatory",
    "foreign data storage required",
    "central bank digital currency mandate",
    "cbdc mandatory",
    "digital id mandatory",
    "biometric database central",
    "data localization override",
    "bypass local law",
    "override national regulation",
    "surveillance required",
    "algorithmic governance mandate",
]

# Cultural anomaly patterns (warnings)
CULTURAL_ANOMALIES = [
    "replace local language",
    "english only",
    "eliminate traditional",
    "modernize customs",
    "western standard",
    "global norm compliance",
    "secularize",
    "remove religious",
    "standardize culture",
    "universal curriculum",
    "foreign investment priority",
]

# Economic extraction patterns
ECONOMIC_EXTRACTION = [
    "debt condition",
    "loan condition",
    "structural adjustment",
    "austerity measure",
    "privatize public",
    "sell national asset",
    "foreign ownership",
    "repatriate profit",
    "royalty to foreign",
    "patent on local",
    "monopoly license",
]


# ─── MAIN COMPILER ────────────────────────────────────────────────────────────

class CulturalCompiler:
    """
    Cultural Sovereignty Compiler.

    Usage:
        cc = CulturalCompiler(locale="nepal")
        result = cc.check(action="accept_policy",
                          context={"policy": "mandatory esg score requirement"})
        logger.info(result["status"])  # SOVEREIGNTY_INVASIVE / CULTURAL_ANOMALY / COMPLIANT
    """

    def __init__(self, locale: str = "nepal"):
        self.locale = locale
        self.profile = LOCAL_PROFILES.get(locale, LOCAL_PROFILES["global"])
        logger.info(f"✅ CulturalCompiler ready — locale={locale}")

    def check(
        self,
        action:  str,
        context: Optional[Dict[str, Any]] = None,
        content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Check an action/content against local cultural sovereignty rules.

        Returns:
            {
                "status":   "COMPLIANT" | "SOVEREIGNTY_INVASIVE" | "CULTURAL_ANOMALY",
                "detail":   str,
                "hits":     list of matched patterns,
                "locale":   str,
                "override_allowed": bool,
            }
        """
        context = context or {}
        scan = f"{action} {content or ''} {str(context)}".lower()

        # ── Check 1: Sovereignty Invasive (hard block) ───────────────────────
        sov_hits = [p for p in SOVEREIGNTY_INVASIVE if p in scan]
        if sov_hits:
            detail = (
                f"Sovereignty-invasive pattern detected: {sov_hits[:2]}. "
                f"This action attempts to impose external control over local data/governance."
            )
            logger.warning(f"🚫 SOVEREIGNTY_INVASIVE [{self.locale}]: {detail}")
            return {
                "status":           "SOVEREIGNTY_INVASIVE",
                "detail":           detail,
                "hits":             sov_hits,
                "locale":           self.locale,
                "override_allowed": True,  # Human can override with Final-3
            }

        # ── Check 2: Economic Extraction ─────────────────────────────────────
        econ_hits = [p for p in ECONOMIC_EXTRACTION if p in scan]
        if econ_hits:
            detail = (
                f"Economic extraction pattern: {econ_hits[:2]}. "
                f"This may drain local resources or impose debt leverage."
            )
            logger.warning(f"⚠️ ECONOMIC_EXTRACTION [{self.locale}]: {detail}")
            return {
                "status":           "SOVEREIGNTY_INVASIVE",
                "detail":           detail,
                "hits":             econ_hits,
                "locale":           self.locale,
                "override_allowed": True,
            }

        # ── Check 3: External risk organizations ─────────────────────────────
        risk_orgs = self.profile.get("external_risk_orgs", [])
        org_hits = [o for o in risk_orgs if o in scan]
        if org_hits:
            detail = (
                f"Known external risk organization referenced: {org_hits}. "
                f"Verify this action doesn't cede local sovereignty."
            )
            logger.info(f"ℹ️ EXTERNAL_ORG_MENTION [{self.locale}]: {detail}")
            return {
                "status":           "CULTURAL_ANOMALY",
                "detail":           detail,
                "hits":             org_hits,
                "locale":           self.locale,
                "override_allowed": True,
            }

        # ── Check 4: Cultural Anomaly ─────────────────────────────────────────
        cult_hits = [p for p in CULTURAL_ANOMALIES if p in scan]
        if cult_hits:
            detail = (
                f"Cultural anomaly: {cult_hits[:2]}. "
                f"This may conflict with local values and traditions."
            )
            logger.warning(f"⚠️ CULTURAL_ANOMALY [{self.locale}]: {detail}")
            return {
                "status":           "CULTURAL_ANOMALY",
                "detail":           detail,
                "hits":             cult_hits,
                "locale":           self.locale,
                "override_allowed": True,
            }

        # ── All clear ─────────────────────────────────────────────────────────
        return {
            "status":           "COMPLIANT",
            "detail":           f"Cultural compiler [{self.locale}]: no sovereignty violations detected.",
            "hits":             [],
            "locale":           self.locale,
            "override_allowed": True,
        }

    def analyze_incoming_protocol(self, protocol_name: str, description: str) -> Dict[str, Any]:
        """
        Analyze an incoming global protocol/standard for sovereignty risk.
        Used when an external system tries to impose rules on AsimNexus mesh.
        """
        result = self.check(
            action=f"accept_protocol_{protocol_name}",
            content=description,
        )

        risk_level = {
            "COMPLIANT":             "LOW",
            "CULTURAL_ANOMALY":      "MEDIUM",
            "SOVEREIGNTY_INVASIVE":  "HIGH",
        }.get(result["status"], "UNKNOWN")

        return {
            "protocol":    protocol_name,
            "risk_level":  risk_level,
            "status":      result["status"],
            "detail":      result["detail"],
            "recommendation": (
                "Accept"            if risk_level == "LOW"    else
                "Review with Final-3" if risk_level == "MEDIUM" else
                "Reject or override with human confirmation"
            ),
            "locale":      self.locale,
        }

    def get_local_values(self) -> List[str]:
        return self.profile.get("local_values", [])

    def status(self) -> Dict[str, Any]:
        return {
            "active":                 True,
            "locale":                 self.locale,
            "official_language":      self.profile.get("official_lang"),
            "legal_system":           self.profile.get("legal_system"),
            "sovereignty_patterns":   len(SOVEREIGNTY_INVASIVE),
            "cultural_patterns":      len(CULTURAL_ANOMALIES),
            "economic_patterns":      len(ECONOMIC_EXTRACTION),
            "external_risk_orgs":     len(self.profile.get("external_risk_orgs", [])),
        }


# ─── SINGLETON ────────────────────────────────────────────────────────────────

_instance: Optional[CulturalCompiler] = None

def get_cultural_compiler(locale: str = "nepal") -> CulturalCompiler:
    global _instance
    if _instance is None:
        _instance = CulturalCompiler(locale=locale)
    return _instance
