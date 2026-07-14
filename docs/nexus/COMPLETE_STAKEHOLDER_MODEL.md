# AsimNexus Complete Stakeholder Operation Model

> **"एउटै व्यक्ति, धेरै भूमिका, तर सबै एउटै Chat बाट, सबै सुरक्षित"**
> *(One Person, Many Roles, but all from the same Chat, all secure)*

## Table of Contents

1. [Overview](#1-overview)
2. [The Three Stakeholders](#2-the-three-stakeholders)
3. [One Person, Many Roles (Multi-Mode System)](#3-one-person-many-roles)
4. [Digital Twin Marketplace (Give Work & Do Work)](#4-digital-twin-marketplace)
5. [3-Confirmation System Across All Modes](#5-3-confirmation-system)
6. [Mode-Based Policy Engine](#6-mode-based-policy-engine)
7. [Complete Architecture Diagram](#7-complete-architecture-diagram)
8. [Integration Points](#8-integration-points)
9. [API Reference](#9-api-reference)
10. [Usage Examples](#10-usage-examples)
11. [File Reference](#11-file-reference)

---

## 1. Overview

AsimNexus is the complete **Digital Nepal** platform that connects all three levels of Nepali society through a single unified bridge:

| Stakeholder | Power Share | Role |
|-------------|-------------|------|
| **Government** 🏛️ | **51%** | Sovereign oversight, constitutional enforcement, veto power |
| **Companies** 🏢 | **49%** | Commercial operations, private sector, economic growth |
| **Citizens** 👤 | **Local-First** | Individual sovereignty, data ownership, digital twin agency |

### Core Philosophy

```
एउटै व्यक्ति → धेरै भूमिका → एउटै Platform → सबै सुरक्षित
(One Person) → (Many Roles) → (One Platform) → (All Secure)
```

### Key Principles

1. **51/49 Power Balance**: Public sector holds 51% decision power, private sector holds 49%
2. **Local-First**: Citizen data stays on their device, never leaves without consent
3. **Data Isolation**: Citizen data NEVER accessible from Company mode
4. **3-Confirmation**: Every action requires human verification (PIN → OTP → Biometric+HSM)
5. **Immutable Audit**: Every action permanently recorded via append-only JSONL
6. **Digital Twin Agency**: Every person's Digital Twin can work autonomously with human oversight

---

## 2. The Three Stakeholders

### 2.1 Government (51%) 🏛️

**How Government Operates in AsimNexus:**

| Function | Description | Module |
|----------|-------------|--------|
| **Policy Making** | Create, amend, and enforce policies | [`core/governance/government_layer.py`](../../core/governance/government_layer.py) |
| **Constitutional Oversight** | Ensure all actions comply with the constitution | [`core/security/immutable_constitution.py`](../../core/security/immutable_constitution.py) |
| **Veto Power** | Issue constitutional, policy, operational, and emergency vetoes | [`core/governance/government_layer.py`](../../core/governance/government_layer.py) |
| **Emergency Declaration** | Declare and resolve emergencies with 51% authority | [`core/governance/government_layer.py`](../../core/governance/government_layer.py) |
| **Compliance & Audit** | Monitor company and citizen compliance | [`core/governance/enterprise_layer.py`](../../core/governance/enterprise_layer.py) |
| **Tax Collection** | Digital tax filing and collection | [`core/nexus_connector.py`](../../core/nexus_connector.py) |
| **License Issuance** | Issue and manage licenses for companies and citizens | [`core/governance/enterprise_layer.py`](../../core/governance/enterprise_layer.py) |
| **Dispute Resolution** | Arbitrate disputes between stakeholders | [`core/nexus_connector.py`](../../core/nexus_connector.py) |

**Government Mode Requirements:**
- ALL actions require **Level-3 Confirmation** (HSM + Biometric)
- All actions are publicly auditable
- 72-hour cooling-off period for irreversible actions
- 90% supermajority required for constitutional amendments

### 2.2 Companies (49%) 🏢

**How Companies Operate in AsimNexus:**

| Company Type | Description | Example |
|-------------|-------------|---------|
| **Global Enterprise** | International companies operating in Nepal | Google Nepal, Microsoft |
| **Local Business** | Nepal-registered businesses | Grocery stores, restaurants |
| **Startup** | Early-stage companies | Tech startups, innovation labs |
| **SME** | Small and medium enterprises | Local manufacturers, services |
| **NGO/Non-Profit** | Social organizations | Charities, foundations |
| **Cooperative** | Member-owned organizations | Farmer cooperatives, savings groups |

**Company Operations:**
- Register licenses through the Enterprise Layer
- Hire employees (citizens) with Digital Twin contracts
- Pay taxes digitally through the Nexus Connector
- Comply with government regulations
- Participate in the marketplace (buy/sell services)
- Stake reputation for quality signaling

**Company Mode Requirements:**
- Standard operations: **Level-2 Confirmation** (OTP/MFA)
- Compliance/High-value: **Level-3 Confirmation** (HSM + Biometric)
- 48-hour cooling-off period for compliance actions

### 2.3 Citizens (Local-First) 👤

**How Citizens Operate in AsimNexus:**

| Capability | Description | Module |
|-----------|-------------|--------|
| **Digital Identity** | Single identity with multiple mode-specific Digital Twins | [`core/identity/enhanced_federated_identity.py`](../../core/identity/enhanced_federated_identity.py) |
| **Digital Twin** | Personal AI clone with consciousness, dreaming, evolution | [`core/mirror/mirror_module.py`](../../core/mirror/mirror_module.py) |
| **Agent Contracts** | Hire out their Digital Twin for work (5/15/30 days) | [`core/agent_contract.py`](../../core/agent_contract.py) |
| **Marketplace** | Buy/sell services through the Digital Twin Marketplace | [`core/marketplace/digital_twin_marketplace.py`](../../core/marketplace/digital_twin_marketplace.py) |
| **Personal Finance** | Manage personal finances, payments, escrow | [`core/nexus_connector.py`](../../core/nexus_connector.py) |
| **Health Records** | Store and share health records with consent | [`core/nexus_connector.py`](../../core/nexus_connector.py) |
| **Education** | Access educational resources and certifications | [`core/nexus_connector.py`](../../core/nexus_connector.py) |
| **Employment** | Find work, apply for jobs, manage contracts | [`core/nexus_connector.py`](../../core/nexus_connector.py) |

**Citizen Mode Requirements:**
- Personal actions: **Level-1 Confirmation** (PIN)
- Financial actions: **Level-2 Confirmation** (OTP/MFA)
- Irreversible actions: **Level-3 Confirmation** (HSM + Biometric)
- 24-hour cooling-off period for irreversible actions

---

## 3. One Person, Many Roles

### 3.1 Multi-Mode System

The [`EnhancedFederatedIdentity`](../../core/identity/enhanced_federated_identity.py) system implements the "एउटै व्यक्ति, धेरै भूमिका" pattern:

```
                    ┌─────────────────────────┐
                    │     Single User ID       │
                    │     (user_abc123)        │
                    └───────────┬─────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
        ┌────────────┐  ┌────────────┐  ┌────────────┐
        │  Citizen   │  │  Company   │  │ Government │
        │   Twin     │  │   Twin     │  │   Twin     │
        └────────────┘  └────────────┘  └────────────┘
                │               │               │
                ▼               ▼               ▼
        ┌─────────────────────────────────────────┐
        │           Hybrid Twin                    │
        │   (Multi-role simultaneous operation)    │
        └─────────────────────────────────────────┘
```

### 3.2 Mode Switching

A user can switch between modes at any time:

```python
# Example: User switches from Citizen to Government mode
identity = get_enhanced_identity()
result = identity.switch_mode(
    user_id="user_abc123",
    target_mode=IdentityMode.GOVERNMENT,
    verification_data={"hsm_signature": "...", "biometric_hash": "..."}
)
# Returns: {"success": True, "previous_mode": "citizen", "new_mode": "government"}
```

### 3.3 Data Isolation Rules

| Source Mode | Target Mode | Access Rule |
|-------------|-------------|-------------|
| Citizen | Citizen | ✅ Full access |
| Citizen | Company | ❌ Denied |
| Citizen | Government | ❌ Denied (except with Level-3 consent) |
| Company | Company | ✅ Full access |
| Company | Citizen | ❌ Denied (data isolation) |
| Company | Government | ✅ Compliance/Audit only |
| Government | Government | ✅ Full access |
| Government | Citizen | ✅ With Level-3 + constitutional approval |
| Government | Company | ✅ Compliance/Audit/Tax |
| Hybrid | Any | ✅ With highest consent level |

### 3.4 Mode Permission Matrix

| Action | Citizen | Company | Government | Hybrid |
|--------|---------|---------|------------|--------|
| identity_verify | SELF | SELF | SELF | SELF |
| data_access | SELF | CONFIRM | APPROVE | APPROVE |
| agent_contract | SELF | SELF | APPROVE | APPROVE |
| personal_finance | SELF | SELF | — | APPROVE |
| health_record | SELF | — | — | APPROVE |
| education | SELF | — | — | APPROVE |
| commerce | CONFIRM | SELF | APPROVE | APPROVE |
| employment | CONFIRM | SELF | — | APPROVE |
| license | APPROVE | APPROVE | SELF | APPROVE |
| tax_filing | CONFIRM | CONFIRM | SELF | APPROVE |
| compliance | — | APPROVE | SELF | APPROVE |
| marketplace | SELF | SELF | APPROVE | APPROVE |
| policy | NOTIFY | NOTIFY | SELF | APPROVE |
| regulation | NOTIFY | NOTIFY | SELF | APPROVE |
| veto | — | — | SELF | APPROVE |
| emergency | — | — | SELF | APPROVE |
| constitutional | — | — | APPROVE | APPROVE |
| audit | SELF | CONFIRM | SELF | APPROVE |
| cross_consent | — | APPROVE | SELF | APPROVE |
| dispute | CONFIRM | CONFIRM | SELF | APPROVE |
| governance | — | — | SELF | APPROVE |
| consensus | — | — | SELF | APPROVE |

**Legend:**
- **SELF**: User can act alone
- **NOTIFY**: Must notify affected parties
- **CONFIRM**: Must get confirmation
- **APPROVE**: Must get approval from higher authority
- **VETO**: Subject to government veto
- **—**: Not available in this mode

---

## 4. Digital Twin Marketplace

### 4.1 Give Work & Do Work Model

The [`DigitalTwinMarketplace`](../../core/marketplace/digital_twin_marketplace.py) implements the complete "Give Work & Do Work" lifecycle:

```
                    ┌─────────────────────┐
                    │  Agent Creates       │
                    │  Listing             │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Client Discovers    │
                    │  & Hires Agent       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Contract Created    │
                    │  (5/15/30 days)      │
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    │                     │
                    ▼                     ▼
            ┌──────────────┐    ┌──────────────┐
            │ 3-Confirmation│    │  Escrow       │
            │  (PIN→OTP→HSM)│    │  Payment      │
            └──────────────┘    └──────────────┘
                    │                     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Agent's Twin       │
                    │  Performs Work      │
                    │  (Agent Mode)       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Milestones         │
                    │  Delivered &        │
                    │  Verified           │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Escrow Released    │
                    │  Contract Complete  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Ratings &          │
                    │  Reputation Update  │
                    └─────────────────────┘
```

### 4.2 Work Categories

| Category | Description | Examples |
|----------|-------------|----------|
| **CODING** | Software development | Web apps, mobile apps, APIs |
| **VIDEO** | Video production/editing | YouTube videos, ads, films |
| **MUSIC** | Music composition/production | Songs, jingles, scores |
| **DESIGN** | Graphic design, UI/UX | Logos, websites, branding |
| **WRITING** | Content writing, translation | Articles, books, translations |
| **ANALYSIS** | Data analysis, research | Reports, analytics, insights |
| **EDUCATION** | Teaching, tutoring | Online courses, mentoring |
| **CONSULTING** | Business/technical consulting | Strategy, architecture, advice |
| **ADMIN** | Administrative tasks | Scheduling, email, data entry |
| **CUSTOM** | Custom/other services | Anything else |

### 4.3 Contract Tiers

| Tier | Duration | Description |
|------|----------|-------------|
| **TRIAL** | 5 days | Limited scope, high oversight, lower price |
| **STANDARD** | 15 days | Standard scope, balanced oversight |
| **EXTENDED** | 30 days | Full scope, periodic audit, higher price |

### 4.4 Agent Modes

| Mode | Description |
|------|-------------|
| **PUBLIC** | Digital Twin works autonomously, visible to all marketplace users |
| **PRIVATE** | Digital Twin works with human oversight, limited visibility |
| **HYBRID** | Digital Twin works autonomously but human can intervene at any time |

### 4.5 Escrow System

The escrow system ensures secure payment holding:

1. **Client deposits** funds into escrow when contract is confirmed
2. **Agent's Twin performs** the work
3. **Milestones are delivered** and verified by client
4. **Escrow is released** to agent upon completion
5. **Disputes** are resolved by government arbitrator

### 4.6 Reputation Staking

Agents can stake reputation on their listings to signal quality:
- Higher stake = higher trust = more clients
- Stake can be slashed for poor performance
- Reputation is earned through completed contracts and ratings

---

## 5. 3-Confirmation System

### 5.1 Confirmation Levels

The [`ModeConfirmationSystem`](../../core/security/mode_confirmation.py) implements mode-aware 3-confirmation:

```
Level-1 (PIN)     →  Level-2 (OTP/MFA)  →  Level-3 (HSM+Bio)
    │                      │                       │
    ▼                      ▼                       ▼
Simple actions      Financial actions       Irreversible actions
Profile updates     Commerce                Constitutional changes
Data access         Agent contracts         Veto/Emergency
                    License applications    Cross-consent
                    Tax filing              Governance
```

### 5.2 Mode-Specific Confirmation Rules

| Mode | Default Level | Financial Level | Critical Level | Cooling Period |
|------|---------------|-----------------|----------------|----------------|
| **Citizen** | Level-1 (PIN) | Level-2 (OTP) | Level-3 (HSM+Bio) | 24 hours |
| **Company** | Level-2 (OTP) | Level-3 (HSM+Bio) | Level-3 (HSM+Bio) | 48 hours |
| **Government** | Level-3 (HSM+Bio) | Level-3 (HSM+Bio) | Level-3 (HSM+Bio) | 72 hours |
| **Hybrid** | Level-3 (HSM+Bio) | Level-3 (HSM+Bio) | Level-3 (HSM+Bio) | 72 hours |

### 5.3 Escalation Path

If a user cannot complete a lower level, they can escalate:

```
Level-1 Failed → Escalate to Level-2 (OTP sent to registered device)
Level-2 Failed → Escalate to Level-3 (HSM + Biometric required)
Level-3 Failed → Action denied, cooling period begins
```

### 5.4 Cooling-Off Periods

After certain irreversible actions, a cooling-off period is enforced:

| Action | Cooling Period | Purpose |
|--------|---------------|---------|
| Constitutional amendment | 72 hours | Prevent hasty constitutional changes |
| Veto issuance | 72 hours | Allow for review and appeal |
| Emergency declaration | 72 hours | Prevent abuse of emergency powers |
| Cross-consent override | 72 hours | Protect stakeholder rights |
| Tax filing (large) | 48 hours | Prevent financial errors |
| Compliance action | 48 hours | Allow for compliance review |

---

## 6. Mode-Based Policy Engine

### 6.1 Policy Checking Flow

The [`ModePolicyEngine`](../../core/policy/mode_policy_engine.py) checks every action:

```
User Action
    │
    ▼
┌─────────────────────┐
│ 1. Mode Detection   │  ← Which mode is the user in?
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 2. Action Lookup    │  ← What action is being performed?
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ 3. Permission Check │  ← Is this action allowed in this mode?
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
 ALLOWED       PENDING/DENIED
    │             │
    ▼             ▼
┌────────┐  ┌──────────────┐
│ Execute │  │ 4. Consent   │
│ Action  │  │    Check     │
└────────┘  └──────┬───────┘
                   │
            ┌──────┴──────┐
            │             │
            ▼             ▼
       SELF/CONFIRM   APPROVE/VETO
            │             │
            ▼             ▼
       ┌────────┐  ┌──────────────┐
       │ Execute │  │ 5. Route to  │
       │ Action  │  │  Authority   │
       └────────┘  └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │ 6. Cross-    │
                   │    Mode      │
                   │    Consent   │
                   └──────┬───────┘
                          │
                          ▼
                   ┌──────────────┐
                   │ 7. Execute   │
                   │    or Deny   │
                   └──────────────┘
```

### 6.2 Policy Rules

Custom policy rules can be added to override defaults:

```python
# Example: Add a rule that requires government approval for all AI contracts
rule = PolicyRule(
    rule_id="rule_ai_contracts",
    scope=PolicyScope.GLOBAL,
    mode="ALL",
    action="agent_contract",
    consent_required=ConsentLevel.APPROVE,
    conditions={"ai_contract": True},
    priority=100,
    description="All AI agent contracts require government approval",
)
engine.add_rule(rule)
```

### 6.3 Cross-Mode Access Control

The policy engine enforces strict data isolation:

| Access Pattern | Allowed? | Condition |
|---------------|----------|-----------|
| Citizen → own data | ✅ Yes | Always |
| Company → citizen data | ❌ No | Never |
| Government → citizen data | ✅ Yes | Level-3 + constitutional approval |
| Government → company data | ✅ Yes | Compliance/Audit only |
| Company → government data | ❌ No | Never |
| Hybrid → any data | ✅ Yes | Highest consent level required |

---

## 7. Complete Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ASIMNEXUS PLATFORM                                 │
│                        Digital Nepal - Complete Bridge                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     NEXUS CONNECTOR (core/nexus_connector.py)         │  │
│  │              Unified Bridge for All Stakeholder Modes                 │  │
│  │                                                                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐             │  │
│  │  │ CITIZEN  │  │ COMPANY  │  │GOVERNMENT│  │  HYBRID  │             │  │
│  │  │  Mode    │  │  Mode    │  │  Mode    │  │  Mode    │             │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘             │  │
│  │       │             │             │             │                    │  │
│  │       └─────────────┼─────────────┼─────────────┘                    │  │
│  │                     │             │                                  │  │
│  │                     ▼             ▼                                  │  │
│  │           ┌─────────────────────────────┐                            │  │
│  │           │   Cross-Consent & Routing   │                            │  │
│  │           └─────────────────────────────┘                            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │              ENHANCED FEDERATED IDENTITY                              │  │
│  │         (core/identity/enhanced_federated_identity.py)                │  │
│  │                                                                       │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐               │  │
│  │  │ Citizen Twin │  │ Company Twin │  │Government Twin│               │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘               │  │
│  │                                                                       │  │
│  │  ┌──────────────────────────────────────────────────────────────────┐ │  │
│  │  │              Hybrid Twin (Multi-Role)                            │ │  │
│  │  └──────────────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │              DIGITAL TWIN MARKETPLACE                                │  │
│  │         (core/marketplace/digital_twin_marketplace.py)               │  │
│  │                                                                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │  │
│  │  │ Listings │  │Contracts │  │ Escrow   │  │Reputation│            │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │              3-CONFIRMATION SYSTEM                                    │  │
│  │         (core/security/mode_confirmation.py)                          │  │
│  │                                                                       │  │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────┐                       │  │
│  │  │ Level-1  │ →  │ Level-2  │ →  │ Level-3  │                       │  │
│  │  │   PIN    │    │ OTP/MFA  │    │HSM+Bio   │                       │  │
│  │  └──────────┘    └──────────┘    └──────────┘                       │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │              MODE POLICY ENGINE                                       │  │
│  │         (core/policy/mode_policy_engine.py)                           │  │
│  │                                                                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │  │
│  │  │Permission│  │  Rules   │  │  Audit   │  │  Cross-  │            │  │
│  │  │  Matrix  │  │  Engine  │  │   Log    │  │  Mode    │            │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │              EXISTING CORE MODULES                                    │  │
│  │                                                                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │  │
│  │  │ Agent    │  │ Mirror   │  │Orchestr. │  │Governance│            │  │
│  │  │ Contract │  │ Module   │  │          │  │ Layers   │            │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │  │
│  │                                                                       │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐            │  │
│  │  │Power     │  │Immutable │  │Level-3   │  │Stakehold.│            │  │
│  │  │Balance   │  │Constit.  │  │Confirm   │  │Coord.    │            │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘            │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                    │                                        │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │              API ROUTES                                               │  │
│  │                                                                       │  │
│  │  ┌──────────┐  ┌──────────────────┐  ┌──────────────────┐           │  │
│  │  │ /api/    │  │ /api/dtm/        │  │ /api/nexus/      │           │  │
│  │  │nexus/*   │  │ (Marketplace)    │  │ (Nexus Bridge)   │           │  │
│  │  └──────────┘  └──────────────────┘  └──────────────────┘           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 8. Integration Points

### 8.1 Module Dependencies

```
nexus_connector.py
  ├── enhanced_federated_identity.py  (mode switching, twin management)
  ├── government_layer.py             (51% sovereign control)
  ├── enterprise_layer.py             (49% commercial operations)
  ├── stakeholder_coordinator.py      (multi-stakeholder consensus)
  ├── power_balance_constitution.py   (51/49 balance enforcement)
  ├── level3_confirmation.py          (3-layer human verification)
  ├── agent_contract.py               (5/15/30 day contracts)
  ├── mirror_module.py                (Digital Twin consciousness)
  └── orchestrator.py                 (intent → plan → execution)

digital_twin_marketplace.py
  ├── agent_contract.py               (contract lifecycle)
  ├── nexus_connector.py              (mode routing, cross-consent)
  ├── enhanced_federated_identity.py  (Digital Twin management)
  └── mode_confirmation.py            (3-confirmation)

mode_confirmation.py
  ├── level3_confirmation.py          (existing 3-layer verification)
  ├── nexus_connector.py              (mode routing)
  └── enhanced_federated_identity.py  (multi-mode identity)

mode_policy_engine.py
  ├── nexus_connector.py              (MODE_PERMISSION_MATRIX)
  ├── policy_engine.py                (existing policy engine)
  ├── permissions.py                  (existing permissions verifier)
  ├── immutable_constitution.py       (constitutional compliance)
  ├── power_balance_constitution.py   (51/49 balance)
  └── stakeholder_coordinator.py      (multi-stakeholder coordination)
```

### 8.2 Data Flow

```
User Request
    │
    ▼
┌─────────────────────┐
│  API Route          │  routes/nexus.py, routes/digital_twin_marketplace.py
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Policy Engine      │  core/policy/mode_policy_engine.py
│  (Check Permission) │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼             ▼
 ALLOWED       NEEDS CONSENT
    │             │
    ▼             ▼
┌────────┐  ┌─────────────────────┐
│ Execute│  │ Confirmation System │  core/security/mode_confirmation.py
│ Action │  │ (Level-1/2/3)      │
└────────┘  └──────────┬──────────┘
                       │
                  ┌────┴────┐
                  │         │
                  ▼         ▼
             APPROVED    REJECTED
                  │         │
                  ▼         ▼
             ┌────────┐  ┌────────┐
             │ Execute│  │ Deny   │
             │ Action │  │ Action │
             └────────┘  └────────┘
                  │
                  ▼
             ┌─────────────────────┐
             │ Nexus Connector     │  core/nexus_connector.py
             │ (Route to correct   │
             │  stakeholder mode)  │
             └──────────┬──────────┘
                        │
                  ┌─────┴─────┐
                  │           │
                  ▼           ▼
           ┌──────────┐  ┌──────────┐
           │ Government│  │ Company  │
           │ (51%)     │  │ (49%)    │
           └──────────┘  └──────────┘
                  │           │
                  └─────┬─────┘
                        │
                        ▼
                  ┌──────────────┐
                  │ Citizen      │
                  │ (Local-First)│
                  └──────────────┘
                        │
                        ▼
                  ┌─────────────────────┐
                  │ Immutable Audit Log │  Append-only JSONL
                  └─────────────────────┘
```

---

## 9. API Reference

### 9.1 Nexus Connector API (`/api/nexus/*`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/nexus/session/create` | Create a new session in a mode |
| POST | `/api/nexus/session/switch-mode` | Switch session mode |
| GET | `/api/nexus/session/{session_id}` | Get session details |
| GET | `/api/nexus/user/{user_id}/sessions` | Get user's sessions |
| POST | `/api/nexus/session/{session_id}/end` | End a session |
| POST | `/api/nexus/action` | Process an action |
| GET | `/api/nexus/action/{action_id}` | Get action details |
| POST | `/api/nexus/consent/respond` | Respond to consent request |
| GET | `/api/nexus/consent/pending` | Get pending consents |
| POST | `/api/nexus/identity/register` | Register a new user |
| POST | `/api/nexus/identity/switch-mode` | Switch identity mode |
| GET | `/api/nexus/identity/{user_id}/twins` | Get user's Digital Twins |
| GET | `/api/nexus/identity/{user_id}/switch-history` | Get mode switch history |
| GET | `/api/nexus/status` | System status |
| GET | `/api/nexus/stats` | Comprehensive statistics |
| GET | `/api/nexus/modes` | List all available modes |

### 9.2 Digital Twin Marketplace API (`/api/dtm/*`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/dtm/listings` | Create a new listing |
| POST | `/api/dtm/listings/{id}/publish` | Publish a listing |
| PUT | `/api/dtm/listings/{id}` | Update a listing |
| POST | `/api/dtm/listings/{id}/pause` | Pause a listing |
| POST | `/api/dtm/listings/{id}/activate` | Activate a listing |
| POST | `/api/dtm/listings/{id}/archive` | Archive a listing |
| GET | `/api/dtm/listings/{id}` | Get listing details |
| GET | `/api/dtm/listings` | Search listings |
| GET | `/api/dtm/user/{id}/listings` | Get user's listings |
| POST | `/api/dtm/contracts/propose` | Propose a contract |
| POST | `/api/dtm/contracts/{id}/confirm` | Confirm a contract |
| POST | `/api/dtm/contracts/{id}/complete` | Complete a contract |
| POST | `/api/dtm/contracts/{id}/cancel` | Cancel a contract |
| POST | `/api/dtm/contracts/{id}/dispute` | Dispute a contract |
| POST | `/api/dtm/contracts/{id}/resolve` | Resolve a dispute |
| POST | `/api/dtm/contracts/{id}/rate` | Rate a completed contract |
| GET | `/api/dtm/contracts/{id}` | Get contract details |
| GET | `/api/dtm/user/{id}/contracts` | Get user's contracts |
| GET | `/api/dtm/escrow/{id}` | Get escrow details |
| GET | `/api/dtm/contracts/{id}/escrow` | Get contract escrow |
| POST | `/api/dtm/listings/{id}/stake` | Stake reputation |
| POST | `/api/dtm/listings/{id}/unstake` | Unstake reputation |
| GET | `/api/dtm/contracts/{id}/agent-instructions` | Get agent work instructions |
| GET | `/api/dtm/status` | Marketplace system status |
| GET | `/api/dtm/stats` | Marketplace statistics |

### 9.3 Confirmation System API (`/api/confirm/*`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/confirm/request` | Request confirmation for an action |
| POST | `/api/confirm/{id}/approve` | Approve a confirmation request |
| POST | `/api/confirm/{id}/reject` | Reject a confirmation request |
| POST | `/api/confirm/{id}/escalate` | Escalate to higher level |
| GET | `/api/confirm/{id}` | Get confirmation request details |
| GET | `/api/confirm/pending` | Get pending confirmations |
| GET | `/api/confirm/user/{id}/history` | Get user's confirmation history |
| GET | `/api/confirm/cooling` | Get active cooling periods |
| GET | `/api/confirm/status` | Confirmation system status |
| GET | `/api/confirm/stats` | Confirmation system statistics |

### 9.4 Policy Engine API (`/api/policy/*`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/policy/check` | Check if an action is allowed |
| POST | `/api/policy/check-cross-mode` | Check cross-mode access |
| POST | `/api/policy/rules` | Add a custom policy rule |
| PUT | `/api/policy/rules/{id}` | Update a policy rule |
| DELETE | `/api/policy/rules/{id}` | Remove a policy rule |
| GET | `/api/policy/rules` | List policy rules |
| GET | `/api/policy/permissions/{mode}` | Get permissions for a mode |
| GET | `/api/policy/audit` | Get policy audit log |
| GET | `/api/policy/status` | Policy engine status |
| GET | `/api/policy/stats` | Policy engine statistics |

---

## 10. Usage Examples

### 10.1 Citizen: Hire a Digital Twin for Design Work

```python
import httpx
import asyncio

async def hire_design_twin():
    async with httpx.AsyncClient() as client:
        # 1. Search for design twins
        search = await client.get(
            "http://localhost:8000/api/dtm/listings",
            params={"category": "design", "query": "logo", "page": 1, "limit": 10}
        )
        listings = search.json()["data"]["listings"]
        
        if not listings:
            print("No design twins available")
            return
        
        # 2. Pick the best listing
        best = listings[0]
        print(f"Hiring: {best['title']} by {best['user_id']}")
        
        # 3. Propose a 5-day trial contract
        contract = await client.post(
            "http://localhost:8000/api/dtm/contracts/propose",
            json={
                "listing_id": best["listing_id"],
                "client_id": "citizen_user_123",
                "title": "Logo Design for Startup",
                "description": "Need a modern logo for my tech startup",
                "tier": "trial",
                "price": 5000,
                "currency": "NPR",
                "milestones": [
                    {"name": "Concepts", "description": "3 initial concepts", "due_in_days": 2},
                    {"name": "Revisions", "description": "2 rounds of revisions", "due_in_days": 3},
                    {"name": "Final", "description": "Final files delivery", "due_in_days": 5},
                ],
                "confirmation_level": "level_2",
            }
        )
        contract_id = contract.json()["data"]["contract_id"]
        
        # 4. Confirm with Level-2 (OTP)
        confirm = await client.post(
            f"http://localhost:8000/api/dtm/contracts/{contract_id}/confirm",
            json={
                "user_id": "citizen_user_123",
                "confirmation_data": {
                    "otp": "123456",
                    "method": "sms"
                }
            }
        )
        print(f"Contract confirmed: {confirm.json()}")
        
        # 5. Wait for work to complete, then rate
        rate = await client.post(
            f"http://localhost:8000/api/dtm/contracts/{contract_id}/rate",
            json={"user_id": "citizen_user_123", "rating": 4.5}
        )
        print(f"Rated: {rate.json()}")

# Run
asyncio.run(hire_design_twin())
```

### 10.2 Company: Register and Hire Employees

```python
import httpx
import asyncio

async def company_operations():
    async with httpx.AsyncClient() as client:
        # 1. Switch to Company mode
        session = await client.post(
            "http://localhost:8000/api/nexus/session/create",
            json={
                "user_id": "company_ceo_456",
                "mode": "company",
                "metadata": {"organization": "TechNepal Pvt Ltd"}
            }
        )
        session_id = session.json()["data"]["session_id"]
        
        # 2. Register a company license
        action = await client.post(
            "http://localhost:8000/api/nexus/action",
            json={
                "session_id": session_id,
                "action": "license",
                "payload": {
                    "license_type": "business",
                    "organization": "TechNepal Pvt Ltd",
                    "sector": "technology"
                }
            }
        )
        print(f"License action: {action.json()}")
        
        # 3. Post a job for a Digital Twin developer
        job = await client.post(
            "http://localhost:8000/api/dtm/contracts/propose",
            json={
                "listing_id": "dtm_abc123",  # Developer's listing
                "client_id": "company_ceo_456",
                "title": "Full Stack Developer - 15 days",
                "description": "Build a React + FastAPI web application",
                "tier": "standard",
                "price": 50000,
                "currency": "NPR",
                "confirmation_level": "level_3",  # Company requires Level-3
            }
        )
        print(f"Job posted: {job.json()}")

asyncio.run(company_operations())
```

### 10.3 Government: Policy Enforcement

```python
import httpx
import asyncio

async def government_operations():
    async with httpx.AsyncClient() as client:
        # 1. Switch to Government mode (requires Level-3)
        session = await client.post(
            "http://localhost:8000/api/nexus/session/create",
            json={
                "user_id": "gov_officer_789",
                "mode": "government",
                "metadata": {
                    "department": "Ministry of Technology",
                    "designation": "Digital Nepal Officer"
                }
            }
        )
        session_id = session.json()["data"]["session_id"]
        
        # 2. Issue a policy
        action = await client.post(
            "http://localhost:8000/api/nexus/action",
            json={
                "session_id": session_id,
                "action": "policy",
                "payload": {
                    "policy_type": "data_protection",
                    "title": "Digital Nepal Data Protection Policy 2026",
                    "description": "All citizen data must be stored locally",
                    "sector": "technology",
                    "enforcement_date": "2026-08-01"
                }
            }
        )
        print(f"Policy action: {action.json()}")
        
        # 3. Check compliance of a company
        check = await client.post(
            "http://localhost:8000/api/policy/check-cross-mode",
            json={
                "source_mode": "government",
                "target_mode": "company",
                "action": "compliance",
                "source_user_id": "gov_officer_789",
                "target_user_id": "company_ceo_456"
            }
        )
        print(f"Compliance check: {check.json()}")

asyncio.run(government_operations())
```

### 10.4 One Person, Multiple Roles (Mode Switching)

```python
import httpx
import asyncio

async def multi_role_user():
    """Example: Same person operating in all three modes."""
    async with httpx.AsyncClient() as client:
        user_id = "multi_role_user_001"
        
        # 1. Register user with all four Digital Twins
        register = await client.post(
            "http://localhost:8000/api/nexus/identity/register",
            json={
                "user_id": user_id,
                "display_name": "Digital Nepal Citizen",
                "create_all_twins": True
            }
        )
        print(f"Registered: {register.json()}")
        
        # 2. As CITIZEN: Hire a designer
        citizen_session = await client.post(
            "http://localhost:8000/api/nexus/session/create",
            json={"user_id": user_id, "mode": "citizen"}
        )
        print(f"Citizen session: {citizen_session.json()}")
        
        # 3. Switch to COMPANY mode
        switch = await client.post(
            "http://localhost:8000/api/nexus/identity/switch-mode",
            json={
                "user_id": user_id,
                "target_mode": "company",
                "verification_data": {"hsm_signature": "...", "biometric_hash": "..."}
            }
        )
        print(f"Switched to Company: {switch.json()}")
        
        # 4. As COMPANY: Post a job listing
        company_session = await client.post(
            "http://localhost:8000/api/nexus/session/create",
            json={"user_id": user_id, "mode": "company"}
        )
        
        # 5. Switch to GOVERNMENT mode
        switch = await client.post(
            "http://localhost:8000/api/nexus/identity/switch-mode",
            json={
                "user_id": user_id,
                "target_mode": "government",
                "verification_data": {"hsm_signature": "...", "biometric_hash": "..."}
            }
        )
        print(f"Switched to Government: {switch.json()}")
        
        # 6. Get all twins for this user
        twins = await client.get(
            f"http://localhost:8000/api/nexus/identity/{user_id}/twins"
        )
        print(f"All twins: {twins.json()}")

asyncio.run(multi_role_user())
```

---

## 11. File Reference

### New Files Created

| File | Description | Lines |
|------|-------------|-------|
| [`core/nexus_connector.py`](../../core/nexus_connector.py) | Unified bridge connecting Government (51%), Companies (49%), Citizens (Local-First) | ~1311 |
| [`core/identity/enhanced_federated_identity.py`](../../core/identity/enhanced_federated_identity.py) | Multi-Mode Digital Twin system (One Person, Many Roles) | ~507 |
| [`core/marketplace/digital_twin_marketplace.py`](../../core/marketplace/digital_twin_marketplace.py) | Digital Twin Marketplace with Agent Mode (Give Work & Do Work) | ~1050 |
| [`core/security/mode_confirmation.py`](../../core/security/mode_confirmation.py) | Mode-aware 3-Confirmation system (Level-1/2/3 across all modes) | ~550 |
| [`core/policy/mode_policy_engine.py`](../../core/policy/mode_policy_engine.py) | Mode-based policy engine with permission matrix and cross-mode access control | ~500 |
| [`routes/nexus.py`](../../routes/nexus.py) | REST API endpoints for Nexus Connector and Enhanced Federated Identity | ~405 |
| [`routes/digital_twin_marketplace.py`](../../routes/digital_twin_marketplace.py) | REST API endpoints for Digital Twin Marketplace | ~350 |
| [`docs/nexus/NEXUS_CONNECTOR_ARCHITECTURE.md`](../../docs/nexus/NEXUS_CONNECTOR_ARCHITECTURE.md) | Nexus Connector architecture documentation | ~400 |
| [`docs/nexus/COMPLETE_STAKEHOLDER_MODEL.md`](../../docs/nexus/COMPLETE_STAKEHOLDER_MODEL.md) | Complete stakeholder operation model documentation (this file) | ~713 |

### Existing Files Referenced

| File | Description |
|------|-------------|
| [`core/agent_contract.py`](../../core/agent_contract.py) | 5/15/30 day agent contract system |
| [`core/mirror/mirror_module.py`](../../core/mirror/mirror_module.py) | Digital Twin consciousness, dreaming, evolution |
| [`core/orchestrator/orchestrator.py`](../../core/orchestrator/orchestrator.py) | Intent → Plan → Execution pipeline |
| [`core/governance/government_layer.py`](../../core/governance/government_layer.py) | 51% sovereign control with veto power |
| [`core/governance/enterprise_layer.py`](../../core/governance/enterprise_layer.py) | 49% commercial governance |
| [`core/governance/stakeholder_coordinator.py`](../../core/governance/stakeholder_coordinator.py) | Multi-stakeholder coordination |
| [`core/governance/tripartite_router.py`](../../core/governance/tripartite_router.py) | Mode-based routing |
| [`core/security/power_balance_constitution.py`](../../core/security/power_balance_constitution.py) | 51/49 power balance constitution |
| [`core/security/immutable_constitution.py`](../../core/security/immutable_constitution.py) | Formal rules verification engine |
| [`core/security/level3_confirmation.py`](../../core/security/level3_confirmation.py) | 3-layer human verification |
| [`core/policy/policy_engine.py`](../../core/policy/policy_engine.py) | Existing policy engine |
| [`core/policy/permissions.py`](../../core/policy/permissions.py) | Existing permissions verifier |
| [`core/identity/federated_identity.py`](../../core/identity/federated_identity.py) | Original federated identity (base) |
| [`routes/marketplace.py`](../../routes/marketplace.py) | Existing marketplace routes |
| [`routes/stakeholder.py`](../../routes/stakeholder.py) | Existing stakeholder routes |

---

> **AsimNexus = Digital Nepal**
>
> *"एउटै व्यक्ति, धेरै भूमिका, तर सबै एउटै Chat बाट, सबै सुरक्षित"*
>
> One Person, Many Roles, but all from the same Chat, all secure.
