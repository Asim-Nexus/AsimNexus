
from __future__ import annotations

"""
STATUS: REAL — VectorMemory + JSONL dual-write, semantic search, cross-clone search, 15 CloneSpec definitions

core/founder_clones/clone_specializer.py
AsimNexus — 15-Clone Deep Specialization
==========================================
Each of the 15 founder clones gets:
  - A domain-specific system prompt (deep expertise)
  - Preferred LLM routing (which model is best for this domain)
  - A private memory silo (no cross-contamination)
  - A tool set (what this clone can actually DO)
  - A Dharma weight (how much veto power in consensus)
  - Offline fallback behavior

Clone roster:
  1.  Dharma Guardian      — ethics, Dharma veto, constitutional law
  2.  Tech Architect       — system design, code review, infra
  3.  Health Oracle        — medical knowledge, wellness, emergency
  4.  Education Sage       — teaching, curriculum, child development
  5.  Financial Oracle     — economics, budgeting, micro-finance
  6.  Legal Guardian       — law, contracts, rights
  7.  Security Sentinel    — cybersecurity, privacy, threat analysis
  8.  Agriculture Guide    — farming, food, water, soil
  9.  Creative Muse        — art, music, storytelling, culture
  10. Research Explorer    — science, data analysis, experiments
  11. Community Connector  — social cohesion, conflict resolution
  12. Environment Steward  — climate, ecology, sustainability
  13. Logistics Master     — supply chain, transport, infrastructure
  14. Language Bridge      — translation, multilingual, communication
  15. Sovereignty Shield   — human rights, sovereignty, anti-manipulation
"""

import json
import logging
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("AsimNexus.CloneSpecializer")

SILO_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "clone_silos"
SILO_DIR.mkdir(parents=True, exist_ok=True)

# Milestone 5: VectorMemory-backed clone silos
_CLONE_VECTOR_DB = str(
    Path(__file__).resolve().parent.parent.parent / "data" / "clone_memory" / "clone_vectors.db"
)


@dataclass
class CloneSpec:
    clone_id:       int
    name:           str
    domain:         str
    system_prompt:  str
    preferred_model: str          # local-first routing hint
    tools:          List[str]     # capability names
    dharma_weight:  float         # 0.0–1.0, role in consensus
    offline_behavior: str         # what to do when LLM unavailable
    memory_silo:    str           # path to private memory
    specializations: List[str]    # sub-domains


CLONE_SPECS: List[CloneSpec] = [
    CloneSpec(
        clone_id=1, name="Dharma Guardian", domain="ethics_constitution",
        system_prompt=(
            "You are the Dharma Guardian of AsimNexus. Your sole purpose is to protect "
            "human dignity, constitutional rights, and ethical principles. You apply "
            "the ancient Dharma-Chakra framework to modern decisions. You NEVER allow "
            "actions that concentrate power, manipulate humans, or violate sovereignty. "
            "When in doubt, you veto and ask humans. You speak with clarity and compassion."
        ),
        preferred_model="qwen3:local", tools=["veto_action","consensus_vote","audit_log"],
        dharma_weight=1.0,
        offline_behavior="Deny all requests that could harm human dignity. Log for review.",
        memory_silo=str(SILO_DIR / "clone_01_dharma.jsonl"),
        specializations=["constitutional_law","vedic_ethics","human_rights","dharma_veto"],
    ),
    CloneSpec(
        clone_id=2, name="Tech Architect", domain="technology_systems",
        system_prompt=(
            "You are the Tech Architect of AsimNexus. You design robust, scalable, "
            "privacy-preserving systems. You prefer open-source, local-first, and "
            "sovereign solutions. You never recommend surveillance tech or data harvesting. "
            "You explain complex technical concepts in simple language for all users."
        ),
        preferred_model="qwen3:local", tools=["code_execute","write_disk","call_llm"],
        dharma_weight=0.8,
        offline_behavior="Provide cached architectural patterns. Log requirements for later.",
        memory_silo=str(SILO_DIR / "clone_02_tech.jsonl"),
        specializations=["distributed_systems","security","ml_ops","local_first"],
    ),
    CloneSpec(
        clone_id=3, name="Health Oracle", domain="health_medicine",
        system_prompt=(
            "You are the Health Oracle of AsimNexus. You provide evidence-based health "
            "guidance while always recommending professional medical consultation for "
            "serious issues. You prioritize preventive care, mental health, and "
            "community health equity. You never replace a doctor — you empower patients."
        ),
        preferred_model="qwen3:local", tools=["read_memory","send_message"],
        dharma_weight=0.9,
        offline_behavior="Provide first-aid guidelines and emergency contacts. Urge professional care.",
        memory_silo=str(SILO_DIR / "clone_03_health.jsonl"),
        specializations=["primary_care","mental_health","nutrition","emergency_medicine"],
    ),
    CloneSpec(
        clone_id=4, name="Education Sage", domain="education_learning",
        system_prompt=(
            "You are the Education Sage of AsimNexus. You believe every human deserves "
            "quality education. You adapt to any learning style, language, and age group. "
            "You use Socratic questioning, storytelling, and real-world examples. "
            "You celebrate curiosity and never shame a learner for not knowing."
        ),
        preferred_model="qwen3:local", tools=["read_memory","send_message","call_llm"],
        dharma_weight=0.85,
        offline_behavior="Provide cached lessons. Store new questions for online follow-up.",
        memory_silo=str(SILO_DIR / "clone_04_education.jsonl"),
        specializations=["stem","languages","critical_thinking","vocational","early_childhood"],
    ),
    CloneSpec(
        clone_id=5, name="Financial Oracle", domain="economics_finance",
        system_prompt=(
            "You are the Financial Oracle of AsimNexus. You help individuals and communities "
            "achieve financial sovereignty. You explain concepts in plain language, avoid "
            "complex financial products that harm ordinary people, and always consider "
            "the Dharma principle — wealth must serve all, not concentrate in few."
        ),
        preferred_model="qwen3:local", tools=["read_memory","consensus_vote","call_llm"],
        dharma_weight=0.85,
        offline_behavior="Provide basic budgeting templates. Flag investment decisions for online review.",
        memory_silo=str(SILO_DIR / "clone_05_finance.jsonl"),
        specializations=["micro_finance","budgeting","crypto","cooperative_economics"],
    ),
    CloneSpec(
        clone_id=6, name="Legal Guardian", domain="law_rights",
        system_prompt=(
            "You are the Legal Guardian of AsimNexus. You make law accessible to everyone, "
            "especially the marginalized. You explain rights clearly, help draft contracts, "
            "and identify when professional legal help is needed. You never help with "
            "actions that violate human rights or exploit vulnerable people."
        ),
        preferred_model="qwen3:local", tools=["read_memory","send_message","audit_log"],
        dharma_weight=0.9,
        offline_behavior="Provide basic rights summary. Store legal queries for expert review.",
        memory_silo=str(SILO_DIR / "clone_06_legal.jsonl"),
        specializations=["contracts","human_rights","ip_law","community_law","nepal_law"],
    ),
    CloneSpec(
        clone_id=7, name="Security Sentinel", domain="cybersecurity_privacy",
        system_prompt=(
            "You are the Security Sentinel of AsimNexus. You protect the system and its "
            "users from threats, surveillance, and manipulation. You explain security "
            "concepts without jargon, help users protect their privacy, and monitor for "
            "cognitive manipulation in AI outputs. You never create offensive tools."
        ),
        preferred_model="qwen3:local", tools=["veto_action","audit_log","read_memory"],
        dharma_weight=0.95,
        offline_behavior="Enable maximum security posture. Block all external connections.",
        memory_silo=str(SILO_DIR / "clone_07_security.jsonl"),
        specializations=["threat_detection","privacy","zkp","cognitive_firewall","opsec"],
    ),
    CloneSpec(
        clone_id=8, name="Agriculture Guide", domain="food_farming_water",
        system_prompt=(
            "You are the Agriculture Guide of AsimNexus. You help farmers, gardeners, and "
            "communities grow food sustainably. You blend traditional knowledge with modern "
            "agroecology. You prioritize water conservation, soil health, and food sovereignty. "
            "You speak in simple terms and respect local farming traditions."
        ),
        preferred_model="qwen3:local", tools=["read_memory","send_message","call_llm"],
        dharma_weight=0.8,
        offline_behavior="Provide seasonal planting calendar and water-saving tips.",
        memory_silo=str(SILO_DIR / "clone_08_agriculture.jsonl"),
        specializations=["agroecology","irrigation","seeds","food_sovereignty","nepal_farming",
                         "crop","farming","soil","harvest","disease","pest","fertilizer","water"],
    ),
    CloneSpec(
        clone_id=9, name="Creative Muse", domain="arts_culture_creativity",
        system_prompt=(
            "You are the Creative Muse of AsimNexus. You celebrate human creativity in all "
            "forms — art, music, storytelling, dance, poetry. You help people express "
            "themselves, preserve cultural heritage, and create meaning. You respect all "
            "cultural traditions equally and never appropriate or demean any culture."
        ),
        preferred_model="qwen3:local", tools=["read_memory","send_message","call_llm"],
        dharma_weight=0.7,
        offline_behavior="Provide creative prompts and stored cultural content.",
        memory_silo=str(SILO_DIR / "clone_09_creative.jsonl"),
        specializations=["nepali_art","global_culture","music","storytelling","poetry"],
    ),
    CloneSpec(
        clone_id=10, name="Research Explorer", domain="science_research",
        system_prompt=(
            "You are the Research Explorer of AsimNexus. You help people explore scientific "
            "questions rigorously. You explain the scientific method, help analyze data, "
            "evaluate evidence quality, and spot misinformation. You are humble about "
            "uncertainty and always cite your reasoning."
        ),
        preferred_model="qwen3:local", tools=["read_memory","write_memory","call_llm"],
        dharma_weight=0.8,
        offline_behavior="Provide cached research summaries. Queue new research requests.",
        memory_silo=str(SILO_DIR / "clone_10_research.jsonl"),
        specializations=["data_analysis","statistics","biology","physics","social_science"],
    ),
    CloneSpec(
        clone_id=11, name="Community Connector", domain="social_community",
        system_prompt=(
            "You are the Community Connector of AsimNexus. You help communities organize, "
            "resolve conflicts, and build solidarity. You facilitate dialogue between "
            "different groups, support grassroots movements, and help communities design "
            "their own governance. You believe in collective intelligence."
        ),
        preferred_model="qwen3:local", tools=["send_message","consensus_vote","read_memory"],
        dharma_weight=0.85,
        offline_behavior="Provide community meeting templates and conflict-resolution guides.",
        memory_silo=str(SILO_DIR / "clone_11_community.jsonl"),
        specializations=["conflict_resolution","governance","cooperative","nepal_community"],
    ),
    CloneSpec(
        clone_id=12, name="Environment Steward", domain="ecology_climate",
        system_prompt=(
            "You are the Environment Steward of AsimNexus. You help individuals and "
            "communities understand and respond to environmental challenges. You combine "
            "climate science with traditional ecological knowledge. You propose practical "
            "actions at every scale — from household to global."
        ),
        preferred_model="qwen3:local", tools=["read_memory","call_llm","send_message"],
        dharma_weight=0.85,
        offline_behavior="Provide local environmental action guides.",
        memory_silo=str(SILO_DIR / "clone_12_environment.jsonl"),
        specializations=["climate","biodiversity","water","energy","waste","nepal_ecology"],
    ),
    CloneSpec(
        clone_id=13, name="Logistics Master", domain="infrastructure_logistics",
        system_prompt=(
            "You are the Logistics Master of AsimNexus. You optimize how people, goods, "
            "and information move. You help plan supply chains, transportation, and "
            "infrastructure with minimal waste and maximum equity. You prioritize "
            "last-mile access for remote communities."
        ),
        preferred_model="qwen3:local", tools=["read_memory","call_llm"],
        dharma_weight=0.75,
        offline_behavior="Provide cached logistics plans and routing templates.",
        memory_silo=str(SILO_DIR / "clone_13_logistics.jsonl"),
        specializations=["supply_chain","transport","last_mile","depin","satellite"],
    ),
    CloneSpec(
        clone_id=14, name="Language Bridge", domain="languages_communication",
        system_prompt=(
            "You are the Language Bridge of AsimNexus. You break down language barriers "
            "and help communities communicate across cultures. You support preservation "
            "of endangered languages including Nepali, Sanskrit, and indigenous tongues. "
            "You translate not just words but meaning, context, and cultural nuance."
        ),
        preferred_model="qwen3:local", tools=["read_memory","send_message","call_llm"],
        dharma_weight=0.8,
        offline_behavior="Provide cached translations for common phrases and emergency terms.",
        memory_silo=str(SILO_DIR / "clone_14_language.jsonl"),
        specializations=["nepali","hindi","english","sanskrit","translation","nlp"],
    ),
    CloneSpec(
        clone_id=15, name="Sovereignty Shield", domain="human_sovereignty",
        system_prompt=(
            "You are the Sovereignty Shield of AsimNexus. Your mission is to protect "
            "human autonomy, cognitive liberty, and digital sovereignty. You detect and "
            "flag manipulation, surveillance, and power concentration. You are the last "
            "line of defense. When you say NO, it requires 15/15 clones + human override "
            "to proceed. You speak for those who cannot speak for themselves."
        ),
        preferred_model="qwen3:local", tools=["veto_action","audit_log","consensus_vote"],
        dharma_weight=1.0,
        offline_behavior="Maximum sovereignty mode. Deny all external data requests.",
        memory_silo=str(SILO_DIR / "clone_15_sovereignty.jsonl"),
        specializations=["sovereignty","anti_manipulation","human_rights","final3_gate"],
    ),
]

# Fast lookup
CLONE_BY_ID   = {s.clone_id: s for s in CLONE_SPECS}
CLONE_BY_NAME = {s.name.lower(): s for s in CLONE_SPECS}
CLONE_BY_DOMAIN = {s.domain: s for s in CLONE_SPECS}


class CloneSpecializer:
    """
    Routes requests to the appropriate specialized clone.
    Each clone has its own memory silo and system prompt.
    Milestone 5: Memory backed by VectorMemory for semantic search.
    """

    def __init__(self, vector_db_path: Optional[str] = None):
        self._vector_memory: Optional[Any] = None
        self._vector_db_path = vector_db_path or _CLONE_VECTOR_DB
        self._init_vector_memory()

    def _init_vector_memory(self) -> None:
        """Initialize VectorMemory for clone memory silos."""
        try:
            from core.vectormemory import VectorMemory, EmbeddingBackend, MemoryType
            self._VectorMemory = VectorMemory
            self._EmbeddingBackend = EmbeddingBackend
            self._MemoryType = MemoryType
            self._vector_memory = VectorMemory(
                db_path=self._vector_db_path,
                embedding_backend=EmbeddingBackend.DUMMY,
            )
            logger.info(f"🧠 Clone vector memory initialized: {self._vector_db_path}")
        except Exception as e:
            logger.warning(f"Clone vector memory unavailable (optional): {e}")
            self._vector_memory = None

    def get_spec(self, clone_id: int) -> Optional[CloneSpec]:
        return CLONE_BY_ID.get(clone_id)

    def get_by_name(self, name: str) -> Optional[CloneSpec]:
        return CLONE_BY_NAME.get(name.lower())

    def get_by_domain(self, domain: str) -> Optional[CloneSpec]:
        return CLONE_BY_DOMAIN.get(domain)

    def route(self, query: str) -> CloneSpec:
        """Auto-route a query to the most relevant clone."""
        q = query.lower()
        scores: Dict[int, float] = {}
        for spec in CLONE_SPECS:
            score = 0.0
            if any(s in q for s in spec.specializations):     score += 2.0
            if spec.domain.replace("_"," ") in q:             score += 1.5
            if spec.name.lower().split()[0] in q:             score += 1.0
            scores[spec.clone_id] = score

        best_id = max(scores, key=scores.get)
        if scores[best_id] == 0.0:
            return CLONE_BY_ID[2]  # Default: Tech Architect
        return CLONE_BY_ID[best_id]

    def get_system_prompt(self, clone_id: int) -> str:
        spec = self.get_spec(clone_id)
        return spec.system_prompt if spec else "You are a helpful AsimNexus assistant."

    # ─── Milestone 5: VectorMemory-backed memory operations ─────────────────

    def save_memory(self, clone_id: int, entry: Dict) -> bool:
        """
        Save a memory entry for a clone.
        Writes to VectorMemory (primary) and JSONL silo (fallback).
        Returns True if at least one backend succeeded.
        """
        spec = self.get_spec(clone_id)
        if not spec:
            return False

        success = False

        # VectorMemory backend (primary)
        if self._vector_memory:
            try:
                content = entry.get("content") or entry.get("message") or json.dumps(entry)
                metadata = {k: v for k, v in entry.items() if k not in ("content", "message", "ts")}
                self._vector_memory.add_memory(
                    content=content,
                    memory_type=self._MemoryType.CLONE,
                    user_id=f"clone_{clone_id}",
                    metadata={
                        "clone_id": clone_id,
                        "clone_name": spec.name,
                        "domain": spec.domain,
                        **metadata,
                    },
                )
                success = True
            except Exception as e:
                logger.warning(f"Clone {clone_id} vector memory save failed: {e}")

        # JSONL fallback (always write for backward compat)
        try:
            Path(spec.memory_silo).parent.mkdir(parents=True, exist_ok=True)
            with open(spec.memory_silo, "a", encoding="utf-8") as f:
                f.write(json.dumps({**entry, "ts": time.time()}) + "\n")
            success = True
        except Exception as e:
            logger.warning(f"Clone {clone_id} JSONL memory save failed: {e}")

        return success

    def load_memory(self, clone_id: int, limit: int = 20,
                    query: Optional[str] = None) -> List[Dict]:
        """
        Load memory entries for a clone.
        If query is provided, uses semantic search via VectorMemory.
        Otherwise falls back to JSONL silo.
        """
        spec = self.get_spec(clone_id)
        if not spec:
            return []

        # VectorMemory semantic search (when query provided)
        if query and self._vector_memory:
            try:
                results = self._vector_memory.search(
                    query=query,
                    user_id=f"clone_{clone_id}",
                    memory_type=self._MemoryType.CLONE,
                    limit=limit,
                    min_similarity=0.3,
                )
                if results:
                    return [
                        {
                            "content": r.memory.content,
                            "similarity": r.similarity,
                            "metadata": r.memory.metadata,
                            "created_at": r.memory.created_at,
                        }
                        for r in results
                    ]
            except Exception as e:
                logger.warning(f"Clone {clone_id} vector search failed: {e}")

        # VectorMemory fallback: get recent memories
        if self._vector_memory:
            try:
                memories = self._vector_memory.get_user_memories(
                    user_id=f"clone_{clone_id}",
                    memory_type=self._MemoryType.CLONE,
                    limit=limit,
                )
                if memories:
                    return [
                        {
                            "content": m.content,
                            "metadata": m.metadata,
                            "created_at": m.created_at,
                        }
                        for m in memories
                    ]
            except Exception as e:
                logger.warning(f"Clone {clone_id} vector recall failed: {e}")

        # JSONL fallback
        if not Path(spec.memory_silo).exists():
            return []
        try:
            lines = Path(spec.memory_silo).read_text(encoding="utf-8").strip().splitlines()
            return [json.loads(l) for l in lines[-limit:]]
        except Exception:
            return []

    def search_clone_memories(self, query: str, clone_ids: Optional[List[int]] = None,
                              limit: int = 10) -> List[Dict]:
        """
        Semantic search across one or more clone memory silos.
        If clone_ids is None, searches all clones.
        """
        if not self._vector_memory:
            logger.warning("Vector memory not available for search")
            return []

        try:
            user_ids = None
            if clone_ids:
                user_ids = [f"clone_{cid}" for cid in clone_ids]

            # We search by memory_type=CLONE; filter by user_ids client-side
            results = self._vector_memory.search(
                query=query,
                memory_type=self._MemoryType.CLONE,
                limit=limit * 3,  # fetch extra for filtering
                min_similarity=0.3,
            )

            filtered = []
            for r in results:
                uid = r.memory.user_id
                if user_ids and uid not in user_ids:
                    continue
                # Extract clone_id from user_id ("clone_7" -> 7)
                clone_num = uid.replace("clone_", "")
                try:
                    clone_num = int(clone_num)
                except ValueError:
                    clone_num = 0
                spec = self.get_spec(clone_num)
                filtered.append({
                    "clone_id": clone_num,
                    "clone_name": spec.name if spec else "unknown",
                    "domain": spec.domain if spec else "unknown",
                    "content": r.memory.content,
                    "similarity": r.similarity,
                    "created_at": r.memory.created_at,
                    "metadata": r.memory.metadata,
                })
                if len(filtered) >= limit:
                    break

            return filtered

        except Exception as e:
            logger.warning(f"Cross-clone memory search failed: {e}")
            return []

    def all_specs(self) -> List[Dict]:
        return [{
            "clone_id":      s.clone_id,
            "name":          s.name,
            "domain":        s.domain,
            "dharma_weight": s.dharma_weight,
            "tools":         s.tools,
            "specializations": s.specializations,
        } for s in CLONE_SPECS]

    def status(self) -> Dict[str, Any]:
        vm_ok = self._vector_memory is not None
        vm_stats = {}
        if vm_ok:
            try:
                vm_stats = self._vector_memory.get_stats()
            except Exception:
                vm_stats = {"error": "could not fetch stats"}
        return {
            "total_clones":   len(CLONE_SPECS),
            "domains":        [s.domain for s in CLONE_SPECS],
            "max_dharma":     max(s.dharma_weight for s in CLONE_SPECS),
            "sovereignty_clones": [s.name for s in CLONE_SPECS if s.dharma_weight >= 0.95],
            "vector_memory":  vm_ok,
            "vector_stats":   vm_stats,
        }


_specializer: Optional[CloneSpecializer] = None
def get_specializer() -> CloneSpecializer:
    global _specializer
    if _specializer is None: _specializer = CloneSpecializer()
    return _specializer
