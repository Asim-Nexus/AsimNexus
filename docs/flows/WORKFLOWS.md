# Workflows

> **AsimNexus — Key System Workflows**
> Version: 1.0.0-rc.2 | Last Updated: 2025-07-03

---

## Table of Contents

1. [Governance Workflow](#1-governance-workflow)
2. [Agent Contract Workflow](#2-agent-contract-workflow)
3. [Consensus Workflow](#3-consensus-workflow)
4. [Emergency Workflow](#4-emergency-workflow)
5. [Enterprise License Workflow](#5-enterprise-license-workflow)
6. [Stakeholder Coordination Workflow](#6-stakeholder-coordination-workflow)
7. [Mesh Networking Workflow](#7-mesh-networking-workflow)
8. [Biometric Security Workflow](#8-biometric-security-workflow)
9. [Plugin Marketplace Workflow](#9-plugin-marketplace-workflow)
10. [Data Lake Analytics Workflow](#10-data-lake-analytics-workflow)

---

## 1. Governance Workflow

### 1.1 Policy Approval Flow

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Government│────>│ Power Balance│────>│ Dharma Veto  │────>│ Constitution │
│ Proposes  │     │ Check (51%)  │     │ Engine Check │     │ Compliance   │
│ Policy    │     │              │     │              │     │ Check        │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                    │
                                                                    ▼
                                                          ┌──────────────────┐
                                                          │   Policy Active  │
                                                          │   (All Checks    │
                                                          │    Passed)       │
                                                          └──────────────────┘
```

**Steps:**
1. Government official proposes a policy via [`POST /api/governance/policy/approve`](../routes/governance.py)
2. System checks power balance (51% government threshold)
3. Dharma Veto Engine validates against 6 immutable rules
4. Constitutional compliance verified
5. Policy becomes active across all layers

### 1.2 Veto Flow

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Government│────>│ Dharma Veto  │────>│ Power Balance │────>│ Audit Log    │
│ Issues    │     │ Engine       │     │ Confirmation  │     │ Recorded     │
│ Veto      │     │ Validates    │     │               │     │              │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                    │
                                                                    ▼
                                                          ┌──────────────────┐
                                                          │  Action Blocked  │
                                                          │  (Veto Active)   │
                                                          └──────────────────┘
```

**Steps:**
1. Government issues veto via [`POST /api/governance/veto`](../routes/governance.py)
2. Dharma Veto Engine validates the veto reason
3. Power balance confirms government authority
4. Action is blocked and audit log recorded
5. Veto can be approved via [`POST /api/governance/veto/approve`](../routes/governance.py)

### 1.3 Emergency Declaration Flow

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Emergency │────>│ Dharma Veto  │────>│ Power Balance │────>│ 30-Day Timer │
│ Declared  │     │ Engine Check │     │ Confirmation  │     │ Started      │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                    │
                                                                    ▼
                                                          ┌──────────────────┐
                                                          │ Emergency Powers │
                                                          │ (Max 30 Days)    │
                                                          └──────────────────┘
```

**Steps:**
1. Government declares emergency via [`POST /api/governance/emergency/declare`](../routes/governance.py)
2. Dharma Veto Engine validates emergency reason
3. Power balance confirms government authority
4. 30-day timer starts (max emergency duration)
5. Emergency resolved via [`POST /api/governance/emergency/resolve`](../routes/governance.py)

---

## 2. Agent Contract Workflow

### 2.1 Contract Lifecycle

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Propose  │────>│ Sign         │────>│ Active       │────>│ Complete /   │
│ Contract │     │ (Human+Agent)│     │ (5/15/30 Day)│     │ Expire       │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                    │
                                                                    ▼
                                                          ┌──────────────────┐
                                                          │  Audit Trail    │
                                                          │  (Immutable)    │
                                                          └──────────────────┘
```

### 2.2 Duration Options

| Duration | Use Case | Cooling Off | Auto-Renew |
|----------|----------|-------------|------------|
| **5 Days** | Quick tasks, experiments | 1 day | No |
| **15 Days** | Standard projects | 3 days | Optional |
| **30 Days** | Long-term operations | 7 days | Yes (with approval) |

### 2.3 Contract Creation Flow

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Enterprise│────>│ Define Scope │────>│ Set Duration  │────>│ Propose via  │
│ Initiates │     │ & Permissions│     │ (5/15/30)    │     │ Marketplace  │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                    │
                                                                    ▼
                                                          ┌──────────────────┐
                                                          │  Agent Accepts  │
                                                          │  & Signs        │
                                                          └──────────────────┘
```

**Steps:**
1. Enterprise user initiates contract via [`routes/marketplace.py`](../routes/marketplace.py)
2. Contract scope defined (allowed actions, data access level)
3. Duration selected (5, 15, or 30 days)
4. Contract proposed through marketplace
5. Agent accepts and cryptographically signs
6. Contract becomes active with immutable audit trail

### 2.4 Contract Monitoring

- Expiring contracts warned via [`AgentContractSystem.process_expiring_warnings()`](../core/agent_contract.py:838)
- Expired contracts auto-processed via [`AgentContractSystem.process_expirations()`](../core/agent_contract.py:812)
- Compliance score computed via [`AgentContractSystem._compute_compliance_score()`](../core/agent_contract.py:936)

---

## 3. Consensus Workflow

### 3.1 Standard Consensus

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Proposal │────>│ Vote Round   │────>│ Weighted     │────>│ Result       │
│ Created  │     │ Initiated    │     │ Vote Count   │     │ Applied      │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

**Steps:**
1. Proposal created via [`POST /api/consensus/vote`](../routes/consensus.py)
2. Vote round initiated with all stakeholders
3. Weighted votes counted (government=51%, enterprise=49%, user=100%)
4. Result applied to system

### 3.2 Dharma Veto Check

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│ Action   │────>│ Dharma Veto  │────>│ Allowed /    │
│ Proposed │     │ Engine       │     │ Blocked      │
└──────────┘     └──────────────┘     └──────────────┘
```

The Dharma Veto Engine checks 6 immutable rules:
1. **Sovereignty** — Cannot compromise system sovereignty
2. **Privacy** — Cannot violate user privacy
3. **Security** — Cannot weaken security measures
4. **Fairness** — Cannot create unfair advantages
5. **Transparency** — Cannot hide actions from audit
6. **Balance** — Cannot disrupt 51/49 power balance

---

## 4. Emergency Workflow

### 4.1 Full Emergency Lifecycle

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Detection│────>│ Declaration  │────>│ Active State  │────>│ Resolution   │
│ (Threat) │     │ (Government) │     │ (Max 30 Days) │     │ & Audit      │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                    │
                                                                    ▼
                                                          ┌──────────────────┐
                                                          │  Post-Emergency  │
                                                          │  Review          │
                                                          └──────────────────┘
```

### 4.2 Emergency Powers

During an emergency state, the government gains:
- Temporary override of non-critical policies
- Enhanced monitoring capabilities
- Ability to restrict certain operations
- Fast-track approval for critical actions

### 4.3 Emergency Restrictions

- Maximum duration: 30 days
- Must be reviewed every 7 days
- Cannot override Dharma Veto Engine
- Cannot modify constitution
- Full audit trail required

---

## 5. Enterprise License Workflow

### 5.1 License Lifecycle

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Register │────>│ Verify       │────>│ Active       │────>│ Renew /      │
│ License  │     │ Compliance   │     │ License      │     │ Deactivate   │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### 5.2 License Tiers

| Tier | Max Users | Max Agents | Features |
|------|-----------|------------|----------|
| FREE | 1 | 0 | Basic access |
| STARTER | 5 | 2 | Basic + 1 agent |
| BUSINESS | 50 | 10 | Full marketplace |
| ENTERPRISE | 500 | 100 | All features |
| GOVERNMENT | Unlimited | Unlimited | Full governance |

### 5.3 Registration Flow

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Enterprise│────>│ Choose Tier  │────>│ Submit       │────>│ License      │
│ Registers │     │ & Jurisdiction│    │ Documents    │     │ Activated    │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

**Steps:**
1. Enterprise registers via [`POST /api/enterprise/license/register`](../routes/enterprise.py)
2. License tier and jurisdiction selected
3. Compliance documents submitted
4. License activated with expiry date
5. Compliance checks run periodically

---

## 6. Stakeholder Coordination Workflow

### 6.1 Multi-Stakeholder Action

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Action   │────>│ Required     │────>│ Approvals    │────>│ Consensus    │
│ Proposed │     │ Approvals    │     │ Collected    │     │ Check        │
│          │     │ Determined   │     │              │     │              │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                    │
                                                                    ▼
                                                          ┌──────────────────┐
                                                          │  Action Applied  │
                                                          │  or Escalated    │
                                                          └──────────────────┘
```

### 6.2 Required Approvals by Category

| Category | Government | Enterprise | User |
|----------|:----------:|:----------:|:----:|
| POLICY | ✅ Required | ❌ | ❌ |
| LICENSE | ✅ Required | ✅ Required | ❌ |
| CONTRACT | ❌ | ✅ Required | ✅ Required |
| MODE_CHANGE | ✅ Required | ✅ Required | ✅ Required |
| EMERGENCY | ✅ Required | ❌ | ❌ |
| AMENDMENT | ✅ Required | ✅ Required | ✅ Required |
| COMPLIANCE | ✅ Required | ✅ Required | ❌ |
| AUDIT | ✅ Required | ❌ | ✅ Required |

### 6.3 Escalation Flow

If consensus cannot be reached:
1. Action marked as `REQUIRES_REVIEW`
2. Escalated to higher authority
3. Dharma Veto Engine may be invoked
4. Final decision logged in consensus log

---

## 7. Mesh Networking Workflow

### 7.1 Node Discovery

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ New Node │────>│ LAN Discovery│────>│ Kademlia DHT │────>│ Peer List    │
│ Joins    │     │ (Broadcast)  │     │ (Find Nodes) │     │ Updated      │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                    │
                                                                    ▼
                                                          ┌──────────────────┐
                                                          │  Mesh Connected │
                                                          │  (P2P Ready)    │
                                                          └──────────────────┘
```

### 7.2 Data Sync (CRDT)

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Local    │────>│ CRDT Merge   │────>│ Conflict     │────>│ All Nodes    │
│ Change   │     │ (HLC Timestamp)│    │ Resolution   │     │ Synced       │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### 7.3 NAT Traversal

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│ Client A │────>│ Rendezvous   │────>│ Client B     │
│ (NAT'd)  │     │ Server       │     │ (NAT'd)      │
└──────────┘     └──────────────┘     └──────────────┘
       │                                    │
       └──────────────┬─────────────────────┘
                      ▼
             ┌──────────────────┐
             │  UDP Hole Punch  │
             │  (Direct P2P)    │
             └──────────────────┘
```

---

## 8. Biometric Security Workflow

### 8.1 Hardware Gate Flow

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Threat   │────>│ Biometric    │────>│ Verification │────>│ Access       │
│ Detected │     │ Gate Armed   │     │ (Fingerprint │     │ Granted /    │
│          │     │              │     │  / Face)     │     │ Denied       │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                    │
                                                                    ▼
                                                          ┌──────────────────┐
                                                          │  Audit Record   │
                                                          │  Created        │
                                                          └──────────────────┘
```

### 8.2 Gate States

| State | Description |
|-------|-------------|
| DISARMED | Normal operation, no threat |
| ARMING | Threat detected, gate activating |
| ARMED | Gate active, awaiting biometric |
| VERIFYING | Biometric data being processed |
| GRANTED | Access granted |
| DENIED | Access denied |
| TIMEOUT | Verification timed out |
| ESCALATED | Escalated to admin |
| BYPASS | Emergency bypass activated |

### 8.3 Hard Lock Security

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│ Request  │────>│ Multi-Layer  │────>│ Access       │
│ Access   │     │ Verification │     │ Granted      │
└──────────┘     └──────────────┘     └──────────────┘
                       │
                       ▼
              ┌──────────────────┐
              │  Quantum Key     │
              │  Encryption      │
              └──────────────────┘
```

---

## 9. Plugin Marketplace Workflow

### 9.1 Plugin Lifecycle

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Register │────>│ Version      │────>│ Enable /     │────>│ Unregister   │
│ Plugin   │     │ Management   │     │ Disable      │     │ (Cleanup)    │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### 9.2 Plugin Registration

```python
from core.plugin_marketplace import get_plugin_sdk

sdk = get_plugin_sdk()
sdk.register_plugin(
    plugin_id="my-plugin",
    name="My Plugin",
    version="1.0.0",
    description="Does something useful",
    author="Developer Name",
    entry_point="my_plugin.handler:handle",
    category="analytics",
    permissions=["read:data", "write:data"],
    config_schema={"api_key": {"type": "string", "required": True}}
)
```

---

## 10. Data Lake Analytics Workflow

### 10.1 Data Flow

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ System   │────>│ Snapshot     │────>│ Materialized │────>│ Query &      │
│ Events   │     │ Capture      │     │ View         │     │ Analytics    │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
                                                                    │
                                                                    ▼
                                                          ┌──────────────────┐
                                                          │  Time-Series    │
                                                          │  Aggregation    │
                                                          └──────────────────┘
```

### 10.2 Snapshot Types

| Type | Frequency | Retention |
|------|-----------|-----------|
| System State | Every 5 min | 7 days |
| Governance Actions | Real-time | 90 days |
| Agent Contracts | On change | 1 year |
| Security Events | Real-time | 1 year |
| Performance Metrics | Every 1 min | 30 days |

---

## Related Documentation

| Document | Location |
|----------|----------|
| Governance Model | [`docs/constitution/GOVERNANCE_MODEL.md`](../constitution/GOVERNANCE_MODEL.md) |
| Contract Law | [`docs/constitution/CONTRACT_LAW.md`](../constitution/CONTRACT_LAW.md) |
| Consensus Protocol | [`docs/constitution/CONSENSUS_PROTOCOL.md`](../constitution/CONSENSUS_PROTOCOL.md) |
| Dharma Chakra | [`docs/constitution/DHARMA_CHAKRA.md`](../constitution/DHARMA_CHAKRA.md) |
| Power Balance | [`docs/constitution/POWER_BALANCE_CONSTITUTION.md`](../constitution/POWER_BALANCE_CONSTITUTION.md) |
| Security Framework | [`docs/constitution/SECURITY_FRAMEWORK.md`](../constitution/SECURITY_FRAMEWORK.md) |
