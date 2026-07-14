# AsimNexus Technical Architecture Specification
## Modular Monolith Transition v1.0

**Document Status**: REAL — Production Ready  
**Version**: 1.0  
**Date**: 2026-06-24  
**Author**: AsimNexus Architecture Team

---

## 1. Executive Summary

AsimNexus is transitioning from a prototype to a production-grade Modular Monolith architecture. This specification defines the target architecture, component boundaries, and integration patterns.

### Key Architectural Principles
- **Separation of Concerns**: Each module has a single responsibility
- **Dependency Injection**: Core domain is isolated from external dependencies
- **API Versioning**: `/api/v1/` for future-proof upgrades
- **Event-Driven Integration**: Modules communicate via events, not direct calls
- **Immutability**: Audit trails and state transitions are immutable

---

## 2. Current Architecture State

### 2.1. Implemented Components

| Module | Status | Lines of Code | Key Files |
|--------|--------|---------------|-----------|
| Agent Contract System | ✅ REAL | 1,154 | `core/agent_contract.py` |
| Life Journey | ✅ REAL | 756 | `core/life_journey.py` |
| Dharma Veto Engine | ✅ REAL | 428 | `core/dharma_chakra/veto_engine.py` |
| Power Balance Constitution | ✅ REAL | 726 | `security/power_balance_constitution.py` |
| Offline Sync Engine | ✅ REAL | 872 | `mesh/offline_sync_engine.py` |
| Clone Consensus Voting | ✅ REAL | 336 | `core/consensus/clone_consensus_voting.py` |
| Mirror Module | ✅ REAL | 411 | `core/mirror/*/` |

### 2.2. Current Issues

```
┌─────────────────────────────────────────────────────────────────┐
│                    CURRENT ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────┤
│  simple_backend.py (monolithic)                                 │
│  ├── All routes in single file                                  │
│  ├── Direct imports from core/                                  │
│  ├── No separation of concerns                                  │
│  └── Tight coupling                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Target Modular Monolith Architecture

### 3.1. Directory Structure

```
AsimNexus/
├── apps/
│   ├── backend/
│   │   ├── app.py                    # FastAPI initialization only
│   │   ├── api/v1/
│   │   │   ├── routes/
│   │   │   │   ├── chat.py           # /api/v1/chat
│   │   │   │   ├── gov.py            # /api/v1/gov
│   │   │   │   ├── company.py        # /api/v1/company
│   │   │   │   └── citizen.py        # /api/v1/citizen
│   │   │   ├── middleware/
│   │   │   │   ├── auth.py
│   │   │   │   ├── error_handler.py
│   │   │   │   └── rate_limit.py
│   │   │   └── schemas/
│   │   └── services/
│   │       ├── contract_service.py
│   │       ├── mirror_service.py
│   │       └── power_balance_service.py
│   ├── frontend/                     # React UI (existing)
│   └── mobile/                       # React Native (planned)
├── core/
│   ├── identity/                     # User identity management
│   ├── governance/                   # Government services
│   ├── consensus/                    # 15 Clones voting
│   ├── security/                     # Constitutional rules
│   ├── mesh/                         # P2P networking
│   └── economy/                      # Finance/wallet
├── infrastructure/
│   ├── database/                     # PostgreSQL integration
│   ├── cache/                        # Redis for caching
│   ├── llm_gateway/                  # Multi-provider LLM
│   └── mesh_transport/               # libp2p/WebRTC
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── docs/
    ├── architecture.md
    ├── status.md
    └── api_spec.md
```

### 3.2. Layer Definitions

#### Layer 1: API Layer (`apps/backend/api/v1/`)
- **Responsibility**: HTTP request/response handling
- **Contains**: Routes, schemas, middleware
- **Dependencies**: Services layer only

#### Layer 2: Service Layer (`apps/backend/services/`)
- **Responsibility**: Business logic orchestration
- **Contains**: Contract service, Mirror service, Power Balance service
- **Dependencies**: Core domain, Infrastructure

#### Layer 3: Domain Layer (`core/`)
- **Responsibility**: Pure business logic
- **Contains**: Agent Contract, Life Journey, Dharma Veto, Consensus
- **Dependencies**: None (isolated)

#### Layer 4: Infrastructure Layer (`infrastructure/`)
- **Responsibility**: External integrations
- **Contains**: Database, Cache, LLM Gateway, Mesh Transport
- **Dependencies**: None

---

## 4. Component Specifications

### 4.1. Agent Contract System

**File**: `core/agent_contract.py` (1,154 lines)

**Purpose**: Time-bound AI agent authority with cryptographic binding

**Key Classes**:
```python
class AgentContractSystem:
    - propose_contract()      # Create new contract
    - sign_contract()         # Human signature
    - renew_contract()        # Contract renewal
    - revoke_contract()       # Human revocation + cooling-off
    - check_action_permitted() # Scope enforcement
    - generate_audit()        # Compliance report
    - get_expiring_contracts() # Auto-warn system
```

**State Machine**:
```
PROPOSED → PENDING_SIGNATURE → ACTIVE → EXPIRING_SOON → EXPIRED
                                         ↓
                                    RENEWED (creates new contract)
                                         ↓
                                      REVOKED → COOLING_OFF
                                         ↓
                                     COMPLETED
```

**Integration Points**:
- `core/life_journey.py` — Contracts during Work/Family stages
- `core/dharma_chakra/veto_engine.py` — Action permission checks
- `core/consensus/clone_consensus_voting.py` — 8/15 approval requirement

### 4.2. Life Journey Module

**File**: `core/life_journey.py` (756 lines)

**Purpose**: 6-stage human life tracking

**Life Stages**:
1. **Birth** → Identity creation, guardian assignment
2. **Education** → Age ≥4, enrollment verification
3. **Work** → Age ≥16, skill certification, tax registration
4. **Family** → Age ≥18, stable income, partnership
5. **Retirement** → Age ≥60, pension eligibility
6. **Inheritance** → Will execution, asset transfer

**Key Methods**:
```python
class LifeJourneyModule:
    - create_profile()       # Initialize at Birth stage
    - transition_stage()   # Stage transitions with verification
    - get_available_services() # Services per stage
    - get_life_profile()     # Complete profile
```

### 4.3. Dharma Veto Engine

**File**: `core/dharma_chakra/veto_engine.py` (428 lines)

**Purpose**: Constitutional AI guard for all actions

**Veto Rules**:
```
Rule 1: BLOCK — Harm prevention patterns
Rule 2: REQUIRE_HUMAN — Destructive actions
Rule 3: REQUIRE_HUMAN — Emergency sector
Rule 4: REQUIRE_HUMAN — Government/Legal sector
Rule 5: REQUIRE_HUMAN — Finance ≥$1000
Rule 6: REQUIRE_HUMAN — Privacy/data sharing without consent
```

**ZKP Confirmation Flow**:
```
Action flagged → create_pending() → Human reviews → confirm()/reject() → Proceed/Discard
```

### 4.4. Power Balance Constitution

**File**: `security/power_balance_constitution.py` (726 lines)

**Purpose**: Enforce 51/49 power balance

**Sector Classification**:
| Sector | Control Type | Threshold |
|--------|--------------|-----------|
| Infrastructure | PUBLIC_COORDINATED | 51% public minimum |
| Governance | PUBLIC_COORDINATED | 51% public minimum |
| Healthcare | PUBLIC_COORDINATED | 51% public minimum |
| Education | PUBLIC_COORDINATED | 51% public minimum |
| Commercial | PRIVATE_OPERATED | ≤49% public maximum |
| Finance | MIXED | Case-by-case 40-60% |
| Technology | PRIVATE_OPERATED | ≤49% public maximum |
| Communication | MIXED | Case-by-case 40-60% |

### 4.5. Clone Consensus Voting

**File**: `core/consensus/clone_consensus_voting.py` (336 lines)

**Purpose**: 15 Founder Clones voting for constitutional decisions

**Voting Structure**:
- **Tier 1 (Government)**: 5 clones — 51% sector weight
- **Tier 2 (Company)**: 5 clones — 49% sector weight
- **Tier 3 (Tech/Citizen)**: 5 clones — Execution layer

**Required Quorum**: 8/15 votes for approval

### 4.6. Mirror Module

**Files**: `core/mirror/*.py` (total ~411 lines)

**Purpose**: Digital Twin with self-evolution

**Components**:
- `mirror_module.py` — Main Digital Twin engine
- `lora_engine.py` — Personal LLM adaptation
- `dreaming_engine.py` — Nightly self-learning
- `consciousness.py` — Conscious/Subconscious layers

**Self-Evolution Cycle**:
```
Action → Reflect → Detect Contradiction → LoRA Fine-Tune → Nightly Dream → Pattern Recognition → Insight Generation
```

---

## 5. Data Flow Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   User Input    │────▶│   FastAPI API   │────▶│   Services      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                          │
        ┌─────────────────────────────────────────────────┼─────────────────┐
        ▼                                                 ▼                 ▼
┌─────────────────┐                             ┌─────────────────┐ ┌─────────────────┐
│  Dharma Veto    │◀────────────────────────────│  Core Domain    │ │  Infrastructure │
│  (Guard)        │                             │                 │ │                 │
└─────────────────┘                             │ - Contracts     │ │ - PostgreSQL    │
        │                                       │ - Life Journey  │ │ - Redis         │
        │                                       │ - Consensus     │ │ - LLM Gateway   │
        ▼                                       │ - Mirror        │ │ - Mesh          │
┌─────────────────┐                             └─────────────────┘ └─────────────────┘
│ Human Approval  │                                               │
│ (3-Step ZKP)    │                                               ▼
└─────────────────┘                                       ┌─────────────────┐
        │                                                 │   Response      │
        ▼                                                 │   (via Channels)│
┌─────────────────┐                                       └─────────────────┘
│   Execution     │
│   (Sandboxed)   │
└─────────────────┘
```

---

## 6. Security Architecture

### 6.1. 3-Level Human Confirmation

| Level | Action Type | Requirements |
|-------|-------------|--------------|
| Level-1 | Standard actions | Autonomous execution |
| Level-2 | Payments, data sharing | OTP/PIN confirmation |
| Level-3 | Policy, legal, emergency | HSM + Biometric + 15 Clones consensus |

### 6.2. Immutable Audit Trail

Every action is recorded:
- Action hash (SHA-256)
- Timestamp
- Actor identity
- Result status
- ZKP commitment (Level-3)

---

## 7. Implementation Roadmap

See separate document: `REFACTORING_ROADMAP.md`

---

## 8. Appendix

### 8.1. Environment Variables

```bash
# Agent Contract
ASIM_AGENT_MAX_RENEWALS=3
ASIM_AGENT_COOLING_OFF_HOURS=72
ASIM_AGENT_EXPIRY_WARNING_HOURS=48

# Power Balance
ASIM_POWER_BALANCE_DB_PATH=data/power_balance.jsonl

# Sync Engine
ASIM_SYNC_DB_PATH=data/offline_sync.jsonl
ASIM_SYNC_INTERVAL=15
ASIM_SYNC_BATCH_SIZE=50
ASIM_SYNC_MAX_RETRIES=5
```