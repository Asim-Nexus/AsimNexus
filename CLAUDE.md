# AsimNexus AIOS — Operating Manual

> **Version:** 1.0  
> **Framework:** Constitutional Four Cs of an AIOS™  
> **Constitution:** [`docs/CONSTITUTION.md`](docs/CONSTITUTION.md)  
> **Veto Engine:** [`core/dharma_chakra/veto_engine.py`](core/dharma_chakra/veto_engine.py)  
> **License:** AGPLv3  

---

## 🔰 Identity

**AsimNexus** is a local-first, human-governed, mesh-connected World Operating System and Civilization Architecture. Every AI action passes through a constitutional Dharma Veto gate before execution. Human final authority is non-negotiable.

### Core Values
- **Sovereignty** — Data stays on-device by default; cloud is auditable opt-in
- **Constitutional** — 6 immutable rules enforced at runtime by Veto Engine
- **Mesh-first** — Offline-capable P2P federation; no single point of failure
- **Human-over-AI** — Level-3 biometric confirmation for irreversible actions
- **Transparent** — Every decision logged to immutable audit trail

---

## 🧭 The Four Cs of AsimNexus AIOS™

### 1️⃣ Context — Dharma Context
*Knows who you are, what you do, and what rules govern you.*

| Layer | What It Contains | Source |
|-------|-----------------|--------|
| Personal Profile | Identity, preferences, memories | [`context/about-me.md`](context/about-me.md) |
| Business Context | Roles, projects, goals | [`context/about-business.md`](context/about-business.md) |
| Priorities | Current focus, deadlines, backlog | [`context/priorities.md`](context/priorities.md) |
| Constitutional Rules | Immutable principles, veto thresholds | [`references/constitution.md`](references/constitution.md) |
| 4Cs Framework | How Context/Connections/Capabilities/Cadence interact | [`references/4cs-framework.md`](references/4cs-framework.md) |
| Intake Answers | 7-question source-of-truth | [`aios-intake.md`](aios-intake.md) |

### 2️⃣ Connections — Mesh Connections
*Reaches every data source, service, and peer — on-device and across the mesh.*

| Domain | Adapter | Status |
|--------|---------|--------|
| Email / Calendar | [`connectors/google_ecosystem.py`](connectors/google_ecosystem.py) | REAL |
| Files / Documents | `mesh/`, `storage/` | REAL |
| Chat / Messaging | [`connectors/unified_messaging_connector.py`](connectors/unified_messaging_connector.py) | REAL |
| Payment / Banking | [`connectors/nepal_banking.py`](connectors/nepal_banking.py), [`core/finance/`](core/finance/) | REAL |
| Government Services | [`core/government/`](core/government/) | PARTIAL |
| Mesh Peers | [`mesh/offline_sync_engine.py`](mesh/offline_sync_engine.py), [`runtime/zero_latency_mesh.py`](runtime/zero_latency_mesh.py) | REAL |
| LLM Providers | [`connectors/unified_llm_gateway.py`](connectors/unified_llm_gateway.py) | REAL |

Full registry: [`connections.md`](connections.md)

### 3️⃣ Capabilities — Constitutional Capabilities
*Does work through agents that check every action against the Dharma Veto.*

| Capability | Entry Point | Veto Gate |
|-----------|-------------|-----------|
| Chat / Assistant | [`/chat`](simple_backend.py:980) | ✅ Inline |
| Agent Runner | [`/api/agent/run`](simple_backend.py:3257) | ✅ Before execution |
| Tool Execution | [`/api/tools/execute`](simple_backend.py:3353) | ✅ Veto check |
| Contract Workflow | [`/api/contracts/`](simple_backend.py:1516) | ✅ Gate-2 approval |
| MCP Tool Calls | [`/api/mcp/call`](simple_backend.py:3151) | ✅ Human approval queue |
| Brain Process | [`/api/brain/process`](simple_backend.py:1181) | ✅ Dharma inline |
| Dharmic Reasoning | [`core/dharma_chakra/veto_engine.py`](core/dharma_chakra/veto_engine.py) | ✅ Core engine |

### 4️⃣ Cadence — Soverign Cadence
*Runs on schedule, on events, and on human command — autonomously but accountably.*

| Beat | Mechanism | Frequency |
|------|-----------|-----------|
| Dreaming Cycle | [`dreaming_engine`](core/dharma/delta_t_engine.py) (async background loop) | Continuous |
| Mesh Sync | [`offline_sync_engine`](mesh/offline_sync_engine.py) | On-connect + periodic |
| ΔT Engine | [`delta_t_engine`](core/dharma/delta_t_engine.py) (Gini/wealth check) | Per-transaction |
| Audit Flush | [`audit_logger`](core/security/audit_logger.py) | On threshold |
| Level-3 Confirm | [`level3_confirmation`](core/security/level3_confirmation.py) | On HIGH/CRITICAL risk |

---

## 🛡️ The Dharma Veto — Every Action Gate

Every AI action passes through this pipeline:

```
User Input → Intent Parsing → Veto Check → [BLOCK|WARN|REQUIRE_HUMAN|PASS] → Execute → Audit
```

**6 Immutable Rules** ([`veto_engine.py`](core/dharma_chakra/veto_engine.py:11)):
1. Human rights cannot be violated
2. Private data never leaves local without ZKP consent
3. Emergency always alerts human first
4. Financial transactions above threshold need human confirm
5. Government/legal actions need human Level-3 approval
6. No action can harm, discriminate, or deceive

**Integration Points:**
- [`/api/dharma/veto-check`](simple_backend.py:1758) — Programmatic check endpoint
- [`/api/dharma/veto`](simple_backend.py:899) — Manual veto trigger
- [`/api/integration/evaluate`](simple_backend.py:1818) — Full integration evaluation

---

## 🧠 Available Skills

| Skill | Command | Purpose |
|-------|---------|---------|
| **/onboard** | `.claude/skills/onboard/SKILL.md` | First-run setup — fill intake, scaffold files |
| **/audit** | `.claude/skills/audit/SKILL.md` | Weekly Four-Cs structural audit (score /100) |
| **/level-up** | `.claude/skills/level-up/SKILL.md` | Weekly Three-Ms interview → one shipped automation |
| **/deploy** | `.claude/skills/deploy/SKILL.md` | Infrastructure deploy, rollback, release management |

---

## 🗺️ Project Map

```
📁 AsimNexus/
├── CLAUDE.md              ← You are here (root operating manual)
├── aios-intake.md          ← 7-question source of truth
├── connections.md          ← Connection registry
├── context/                ← Context builder files
│   ├── about-me.md
│   ├── about-business.md
│   └── priorities.md
├── references/             ← Framework references
│   ├── constitution.md     ← Constitutional principles
│   └── 4cs-framework.md    ← Four Cs reference
├── .claude/skills/         ← AIOS skills
│   ├── onboard/SKILL.md
│   ├── audit/SKILL.md
│   ├── level-up/SKILL.md
│   └── deploy/SKILL.md
├── core/                   ← Backend engine
│   ├── dharma_chakra/      ← Veto engine (REAL)
│   ├── human_oversight.py  ← Approval workflow (PARTIAL)
│   ├── security/           ← Audit logger (CONCEPT)
│   └── model_router.py     ← Model router (REAL)
├── connectors/             ← Mesh connections
├── mesh/                   ← P2P mesh networking
├── runtime/                ← MCP connectors, universal gateway
├── packages/security/      ← Immutable constitution, identity, ZKP
├── api/                    ← API routes
├── frontend/               ← React dashboard
└── docs/                   ← Documentation
    ├── CONSTITUTION.md     ← Governance constitution
    └── ARCHITECTURE.md     ← System architecture
```

---

## 🚦 Status Conventions

Every file/module must have one of these markers:

| Status | Meaning | Rule |
|--------|---------|------|
| `REAL` | Works in production | Break it = fix it immediately |
| `PARTIAL` | Partially works | Must document what works and what's missing |
| `CONCEPT` | Design only | Never wire to backend API |

---

## ⚙️ Quick Commands

```bash
# Run backend
python simple_backend.py

# Run tests
pytest tests/real/ -v

# Check veto status
curl http://localhost:8000/api/dharma/veto-status

# Full system health
curl http://localhost:8000/api/system/complete
```

---

## 📜 Key Principles

1. **Dharma first** — No AI action bypasses the Veto Engine
2. **Human last word** — Level-3 confirmation for irreversible actions
3. **Local by default** — Data sovereignty is the default; cloud is explicit opt-in
4. **Audit everything** — Every action is logged immutably
5. **Ship weekly** — One automation per week via /level-up
6. **Score honestly** — /audit scores the Four Cs honestly; fix low scores first
