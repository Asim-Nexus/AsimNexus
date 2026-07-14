
"""
Nepal Digital Dharma Framework
===============================
Ancient Indian/Nepali wisdom integrated into modern computing.

This framework integrates principles from:
- Cultural Compiler (locale-aware cultural rule compilation)
- Cultural Sovereignty (country-specific cultural rule enforcement)
- Delta-T Engine (Proof of Symmetry — network balance)
- Delta-T Integration (influence tracking and veto)
- Delta-T Mesh (mesh network influence coordination)
- Delta-T Production (live network metrics)
- Dharma Veto (constitutional veto system)

For all countries with their own cultural/dharma frameworks.
"""

from .cultural_compiler import CulturalCompiler, get_cultural_compiler
from .cultural_sovereignty import (
    CulturalSovereigntyEngine,
    get_cultural_sovereignty_engine,
    CountryCulturalProfile,
    CulturalRule,
    RulePriority,
    RuleCategory,
)
from .delta_t_engine import DeltaTEngine, run_pos_simulator, NodeState, VetoEvent, PoSReport
from .delta_t_integration import DeltaTIntegration, get_delta_t_integration, InfluenceRecord
from .delta_t_mesh import DeltaTMeshIntegration, get_delta_t_mesh, MeshInfluenceReport
from .delta_t_production import DeltaTProduction, get_delta_t_production, LiveNetworkMetrics
from .dharma_veto import DharmaVeto, get_dharma_veto, VetoEvent as VetoEventDV, VetoResult, VetoSeverity, VetoReason

__version__ = "1.0.0"

# Re-export commonly used names
__all__ = [
    "NepalDigitalDharma",
    "get_nepal_dharma",
    "CulturalCompiler",
    "get_cultural_compiler",
    "CulturalSovereigntyEngine",
    "get_cultural_sovereignty_engine",
    "CountryCulturalProfile",
    "CulturalRule",
    "RulePriority",
    "RuleCategory",
    "DeltaTEngine",
    "run_pos_simulator",
    "NodeState",
    "PoSReport",
    "DeltaTIntegration",
    "get_delta_t_integration",
    "InfluenceRecord",
    "DeltaTMeshIntegration",
    "get_delta_t_mesh",
    "MeshInfluenceReport",
    "DeltaTProduction",
    "get_delta_t_production",
    "LiveNetworkMetrics",
    "DharmaVeto",
    "get_dharma_veto",
    "VetoResult",
    "VetoSeverity",
    "VetoReason",
]


class NepalDigitalDharma:
    """
    Facade for the Nepal Digital Dharma framework.

    Provides a unified interface to all dharma subsystems:
    - Cultural compilation and sovereignty
    - Delta-T influence tracking and veto
    - Constitutional veto enforcement
    """

    def __init__(self):
        self._cultural_compiler = None
        self._sovereignty = None
        self._delta_t = None
        self._veto = None

    @property
    def cultural_compiler(self) -> CulturalCompiler:
        if self._cultural_compiler is None:
            self._cultural_compiler = get_cultural_compiler("nepal")
        return self._cultural_compiler

    @property
    def sovereignty(self) -> CulturalSovereigntyEngine:
        if self._sovereignty is None:
            self._sovereignty = get_cultural_sovereignty_engine()
        return self._sovereignty

    @property
    def delta_t(self) -> DeltaTEngine:
        if self._delta_t is None:
            self._delta_t = DeltaTEngine()
        return self._delta_t

    @property
    def veto(self) -> DharmaVeto:
        if self._veto is None:
            self._veto = get_dharma_veto()
        return self._veto

    def check_action(self, action: str, params: dict = None) -> dict:
        """
        Check an action against all dharma subsystems.
        Returns a dict with pass/fail results from each subsystem.
        """
        result = {
            "passed": True,
            "checks": [],
            "violations": [],
        }
        params = params or {}

        # 1. Cultural compiler check
        try:
            cc_result = self.cultural_compiler.check(action, params)
            result["checks"].append({"system": "cultural_compiler", "passed": cc_result.get("passed", True)})
            if not cc_result.get("passed", True):
                result["passed"] = False
                result["violations"].extend(cc_result.get("violations", []))
        except Exception:
            pass

        # 2. Sovereignty check
        try:
            sv_result = self.sovereignty.check_compliance(action, params.get("country_code", "NP"))
            result["checks"].append({"system": "sovereignty", "passed": sv_result.get("passed", True)})
            if not sv_result.get("passed", True):
                result["passed"] = False
                result["violations"].extend(sv_result.get("violations", []))
        except Exception:
            pass

        # 3. Dharma veto check
        try:
            veto_result = self.veto.check(action, params)
            result["checks"].append({"system": "dharma_veto", "passed": veto_result.passed})
            if not veto_result.passed:
                result["passed"] = False
                result["violations"].append(veto_result.reason.value)
        except Exception:
            pass

        return result


_instance = None


def get_nepal_dharma() -> NepalDigitalDharma:
    """Get or create the singleton NepalDigitalDharma instance."""
    global _instance
    if _instance is None:
        _instance = NepalDigitalDharma()
    return _instance
