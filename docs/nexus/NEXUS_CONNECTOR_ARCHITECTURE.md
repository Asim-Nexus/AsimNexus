# Nexus Connector Architecture — Unified Bridge for Digital Nepal

> **"एउटै व्यक्ति, धेरै भूमिका, तर सबै एउटै Chat बाट, सबै सुरक्षित"**
> *(One Person, Many Roles, but all from the same Chat, all secure)*

## Overview

The **Nexus Connector** is the central bridge that connects all three stakeholder modes in the AsimNexus Digital Nepal platform. It enables a single person to operate as a **Citizen**, **Company CEO**, and **Government Officer** — all through the same unified interface, with complete data isolation and security.

### The Three Stakeholders

| Stakeholder | Power | Role | Data Model |
|------------|-------|------|------------|
| **Government** | 51% | Sovereign oversight, constitutional enforcement, veto power | Centralized policy, public records |
| **Company** | 49% | Commercial operations, licensing, private sector | Licensed operations, compliance |
| **Citizen** | 100% | Individual sovereignty, data ownership, agent contracts | Local-First, personal data |

### Core Principle: 51/49 Power Balance

The 51/49 balance ensures that:
- **Public/Government** coordination holds minimum 51% decision power in critical sectors (Infrastructure, Governance, Healthcare, Education)
- **Private/Company** operation holds maximum 49% decision power (i.e., 51%+ private) in commercial sectors
- **Mixed sectors** (Finance, Communication) are evaluated case-by-case
- **Amendments** require 90% supermajority consensus

---

## Architecture

```
                    ┌─────────────────────────────────┐
                    │         ONE PERSON               │
                    │    (Single User Identity)        │
                    └──────────────┬──────────────────┘
                                   │
                    ┌──────────────▼──────────────────┐
                    │       NEXUS CONNECTOR            │
                    │    (Unified Bridge)              │
                    │                                  │
                    │  ┌──────────┬──────────┬──────┐  │
                    │  │ Citizen  │ Company  │ Gov  │  │
                    │  │(Local-   │ (49%)    │(51%) │  │
                    │  │ First)   │          │      │  │
                    │  └────┬─────┴────┬─────┴──┬───┘  │
                    │       │          │         │      │
                    │       └──────────┼─────────┘      │
                    │            Cross-Consent          │
                    └──────────────────────────────────┘
                                   │
                    ┌──────────────▼──────────────────┐
                    │    3-CONFIRMATION SYSTEM         │
                    │  Level-1: PIN                    │
                    │  Level-2: OTP/MFA                │
                    │  Level-3: HSM + Biometric        │
                    └──────────────────────────────────┘
                                   │
                    ┌──────────────▼──────────────────┐
                    │      IMMUTABLE AUDIT LOG         │
                    │   Every action permanently       │
                    │   recorded and verifiable        │
                    └──────────────────────────────────┘
```

---

## Core Components

### 1. Nexus Connector (`core/nexus_connector.py`)

The central bridge that:
- **Routes actions** to the correct stakeholder mode
- **Manages sessions** across modes (Citizen/Company/Government/Hybrid)
- **Enforces cross-consent** between different modes
- **Checks 51/49 power balance** for constitutional actions
- **Routes to Level-3 confirmation** for high-stakes actions
- **Logs to immutable audit trail**

#### Key Classes

| Class | Purpose |
|-------|---------|
| `NexusConnector` | Main bridge class with session management, action processing, consent management |
| `NexusSession` | A user's current session with mode context |
| `NexusActionRecord` | A single action flowing through the connector |
| `CrossConsentRequest` | A request for consent from another stakeholder mode |

#### Key Enums

| Enum | Values |
|------|--------|
| `NexusMode` | `citizen`, `company`, `government`, `hybrid` |
| `NexusAction` | 20+ action types across all modes |
| `ConsentLevel` | `self`, `notify`, `confirm`, `approve`, `veto` |
| `NexusStatus` | `pending`, `processing`, `approved`, `rejected`, etc. |

### 2. Enhanced Federated Identity (`core/identity/enhanced_federated_identity.py`)

Implements the "One Person, Many Roles" pattern with:
- **Single user_id** → **Four isolated Digital Twins** (Citizen, Company, Government, Hybrid)
- **Strict data isolation** between modes
- **Mode switching** with context preservation
- **Cross-mode access verification** (Citizen data NEVER accessible from Company mode)
- **Immutable audit trail** of all mode switches

#### Key Classes

| Class | Purpose |
|-------|---------|
| `EnhancedFederatedIdentity` | Main identity class with user registration, twin management, mode switching |
| `DigitalTwin` | A mode-specific Digital Twin for a user |
| `ModeSwitchRecord` | Record of a mode switch event |

#### Data Isolation Rules

| From \ To | Citizen | Company | Government |
|-----------|---------|---------|------------|
| **Citizen** | ✅ Full | ❌ Blocked | ❌ Blocked |
| **Company** | ❌ Blocked | ✅ Full | ❌ Blocked (except compliance) |
| **Government** | ✅ Limited (health, edu, emergency) | ✅ Limited (compliance, tax) | ✅ Full |
| **Hybrid** | ✅ Full (audited) | ✅ Full (audited) | ✅ Full (audited) |

### 3. Nexus API Routes (`routes/nexus.py`)

REST API endpoints for all Nexus operations:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/nexus/session/create` | POST | Create a new session |
| `/api/nexus/session/switch-mode` | POST | Switch session mode |
| `/api/nexus/session/{id}` | GET | Get session details |
| `/api/nexus/user/{id}/sessions` | GET | Get user's sessions |
| `/api/nexus/session/{id}/end` | POST | End a session |
| `/api/nexus/action` | POST | Process an action |
| `/api/nexus/action/{id}` | GET | Get action details |
| `/api/nexus/consent/respond` | POST | Respond to consent request |
| `/api/nexus/consent/pending` | GET | Get pending consents |
| `/api/nexus/identity/register` | POST | Register user with twins |
| `/api/nexus/identity/switch-mode` | POST | Switch identity mode |
| `/api/nexus/identity/{id}/twins` | GET | Get user's twins |
| `/api/nexus/identity/{id}/switch-history` | GET | Get switch history |
| `/api/nexus/status` | GET | System status |
| `/api/nexus/stats` | GET | Comprehensive stats |
| `/api/nexus/modes` | GET | List all modes |

---

## Mode Permission Matrix

### Citizen Mode (Local-First)
| Action | Consent Level |
|--------|--------------|
| Identity Verify | Self |
| Data Access | Self |
| Agent Contract | Self |
| Personal Finance | Self |
| Health Record | Self |
| Education | Self |
| Marketplace | Confirm |
| Dispute | Approve |
| Governance | Veto |

### Company Mode (49%)
| Action | Consent Level |
|--------|--------------|
| Commerce | Self |
| Employment | Self |
| License | **Approve** (Government) |
| Tax Filing | **Confirm** (Government) |
| Compliance | **Approve** (Government) |
| Marketplace | Self |
| Dispute | Approve |
| Governance | Veto |

### Government Mode (51%)
| Action | Consent Level |
|--------|--------------|
| Policy | Approve (Company input) |
| Regulation | Confirm (Public notified) |
| Veto | **Self** (Sovereign power) |
| Emergency | Notify (All notified) |
| Constitutional | **Veto** (90% supermajority) |
| Audit | Notify (Transparency) |
| Governance | Veto |

### Hybrid Mode
| Action | Consent Level |
|--------|--------------|
| All Citizen actions | Self |
| Commerce/Employment | Confirm |
| Policy/Regulation | Approve |
| Veto | Approve |
| Cross-Consent | Approve |
| Governance | Veto |

---

## Action Flow

```
User Action
    │
    ▼
┌─────────────────────┐
│ 1. Source Mode      │ ← From session or explicit
│    Detection        │
└─────────┬───────────┘
          │
┌─────────▼───────────┐
│ 2. Target Mode      │ ← Based on action type
│    Routing          │
└─────────┬───────────┘
          │
┌─────────▼───────────┐
│ 3. Consent Check    │ ← Cross-mode consent required?
└─────────┬───────────┘
          │
┌─────────▼───────────┐
│ 4. Level-3 Check    │ ← High-stakes action?
└─────────┬───────────┘
          │
┌─────────▼───────────┐
│ 5. 51/49 Balance    │ ← Constitutional check
│    Check            │
└─────────┬───────────┘
          │
┌─────────▼───────────┐
│ 6. Execute Action   │ ← Route to handler
└─────────┬───────────┘
          │
┌─────────▼───────────┐
│ 7. Audit Log        │ ← Immutable record
└─────────────────────┘
```

---

## Integration Points

### Existing Components

| Component | Integration |
|-----------|-------------|
| `core/governance/stakeholder_coordinator.py` | Multi-stakeholder action coordination |
| `core/governance/government_layer.py` | 51% sovereign control, veto power |
| `core/governance/enterprise_layer.py` | 49% commercial licensing, compliance |
| `core/governance/tripartite_router.py` | Mode-based routing |
| `core/security/power_balance_constitution.py` | 51/49 balance enforcement |
| `core/security/level3_confirmation.py` | 3-layer human verification |
| `core/security/immutable_constitution.py` | Formal rules verification |
| `core/identity/federated_identity.py` | Basic single user → twin mapping |
| `core/mirror/mirror_module.py` | Digital Twin consciousness |
| `core/agent_contract.py` | 5/15/30 day agent contracts |
| `core/orchestrator/orchestrator.py` | Intent → Plan → Execution pipeline |
| `routes/marketplace.py` | Marketplace with jobs, contracts, reputation |
| `routes/stakeholder.py` | Stakeholder coordination API |

### New Components

| Component | File | Purpose |
|-----------|------|---------|
| Nexus Connector | `core/nexus_connector.py` | Unified bridge for all modes |
| Enhanced Federated Identity | `core/identity/enhanced_federated_identity.py` | Multi-mode Digital Twin system |
| Nexus API Routes | `routes/nexus.py` | REST API for all nexus operations |

---

## Security Model

### 3-Confirmation System

| Level | Method | Use Case |
|-------|--------|----------|
| **Level-1** | PIN / Password | Daily operations, low-risk actions |
| **Level-2** | OTP / MFA / TOTP | Medium-risk actions, mode switches |
| **Level-3** | HSM + Biometric | High-stakes: veto, emergency, constitutional |

### Actions Requiring Level-3

- `VETO` — Sovereign veto power
- `EMERGENCY` — Emergency declarations
- `CONSTITUTIONAL` — Constitutional amendments
- `CROSS_CONSENT` — Cross-mode consent
- `GOVERNANCE` — Governance decisions
- `DISPUTE` — Dispute resolution

### Data Isolation

- **Citizen data** is Local-First (stays on user's device)
- **Company data** is isolated from Citizen mode
- **Government data** is isolated from Citizen and Company modes
- **Hybrid mode** can access all, but every access is audited
- **ZKP** (Zero Knowledge Proofs) enable verification without data exposure

---

## Usage Examples

### 1. Register a User (Creates 4 Digital Twins)

```python
from core.identity.enhanced_federated_identity import get_enhanced_identity

identity = get_enhanced_identity()
twins = identity.register_user("user_123", "Ram Sharma")
# Creates: Citizen Twin, Company Twin, Government Twin, Hybrid Twin
```

### 2. Create a Session and Switch Modes

```python
from core.nexus_connector import get_nexus_connector, NexusMode

nexus = get_nexus_connector()

# Start as Citizen
session = nexus.create_session("user_123", NexusMode.CITIZEN)

# Switch to Company mode
nexus.switch_mode(session.session_id, NexusMode.COMPANY)

# Switch to Government mode
nexus.switch_mode(session.session_id, NexusMode.GOVERNMENT)
```

### 3. Process an Action

```python
from core.nexus_connector import NexusAction

# Citizen files taxes (routes to Government for confirmation)
record = await nexus.process_action(
    user_id="user_123",
    action=NexusAction.TAX_FILING,
    payload={"amount": 50000, "fiscal_year": "2081-82"},
    source_mode=NexusMode.CITIZEN,
)
```

### 4. Cross-Consent Flow

```python
# Company requests a license (requires Government approval)
record = await nexus.process_action(
    user_id="company_456",
    action=NexusAction.LICENSE,
    payload={"organization": "TechNepal Pvt Ltd", "tier": "business"},
    source_mode=NexusMode.COMPANY,
)

# Government responds to consent request
nexus.respond_to_consent(
    request_id=record.action_id,
    approved=True,
    response="License approved for TechNepal Pvt Ltd",
)
```

---

## File Reference

| File | Lines | Purpose |
|------|-------|---------|
| [`core/nexus_connector.py`](../../core/nexus_connector.py) | ~1100 | Main Nexus Connector implementation |
| [`core/identity/enhanced_federated_identity.py`](../../core/identity/enhanced_federated_identity.py) | ~400 | Multi-Mode Digital Twin system |
| [`routes/nexus.py`](../../routes/nexus.py) | ~350 | REST API endpoints |
| [`core/governance/stakeholder_coordinator.py`](../../core/governance/stakeholder_coordinator.py) | 415 | Multi-stakeholder coordination |
| [`core/governance/government_layer.py`](../../core/governance/government_layer.py) | 260 | 51% sovereign control |
| [`core/governance/enterprise_layer.py`](../../core/governance/enterprise_layer.py) | 241 | 49% commercial operations |
| [`core/security/power_balance_constitution.py`](../../core/security/power_balance_constitution.py) | 727 | 51/49 balance enforcement |
| [`core/security/level3_confirmation.py`](../../core/security/level3_confirmation.py) | 1499 | 3-layer human verification |
| [`core/agent_contract.py`](../../core/agent_contract.py) | 1155 | 5/15/30 day agent contracts |
| [`core/mirror/mirror_module.py`](../../core/mirror/mirror_module.py) | 662 | Digital Twin consciousness |
| [`core/orchestrator/orchestrator.py`](../../core/orchestrator/orchestrator.py) | 307 | Intent → Plan → Execution |
| [`routes/marketplace.py`](../../routes/marketplace.py) | 1057 | Marketplace with jobs/contracts |
| [`routes/stakeholder.py`](../../routes/stakeholder.py) | 249 | Stakeholder coordination API |
