# Governance Model

> **Three-tier governance: Citizen, Enterprise, Government — how they interact**

## Overview

The AsimNexus governance model implements a three-tier system where Government (51%), Enterprise (49%), and Citizens (100%) each have defined roles, responsibilities, and authority. The model ensures checks and balances while enabling efficient decision-making.

## Tier 1: Government Layer (51%)

### Responsibilities

1. **National Policy** — Define and enforce national digital policies
2. **Regulatory Oversight** — Ensure compliance with national laws
3. **Emergency Management** — Declare and manage digital emergencies
4. **Infrastructure** — Maintain critical national digital infrastructure
5. **Identity Verification** — Verify citizen identities for official purposes

### Authority

- Approve/reject system-wide policy changes
- Issue vetoes on actions threatening national security
- Declare emergency states (max 30 days)
- Audit any system component
- Propose constitutional amendments

### Implementation

The Government Layer is implemented in [`core/governance/government_layer.py`](../core/governance/government_layer.py) and exposed via [`routes/governance.py`](../routes/governance.py).

## Tier 2: Enterprise Layer (49%)

### Responsibilities

1. **Commercial Operations** — Run businesses on the platform
2. **License Management** — Obtain and manage operational licenses
3. **Agent Employment** — Hire AI agents under smart contracts
4. **Compliance** — Ensure operations comply with regulations
5. **Innovation** — Develop new services and features

### Authority

- Register and manage enterprise licenses
- Hire AI agents (5/15/30 day contracts)
- Check compliance of proposed actions
- Access marketplaces and commercial features
- Participate in governance decisions

### Implementation

The Enterprise Layer is implemented in [`core/governance/enterprise_layer.py`](../core/governance/enterprise_layer.py) and exposed via [`routes/enterprise.py`](../routes/enterprise.py).

## Tier 3: Citizen Layer (100%)

### Responsibilities

1. **Self-Governance** — Manage personal digital identity and data
2. **Participation** — Engage in democratic processes
3. **Compliance** — Follow system rules and policies
4. **Contribution** — Contribute to the digital ecosystem

### Authority

- Complete ownership of personal data
- Choose Public, Private, or Agent mode
- Enter into agent contracts
- Vote on governance proposals
- Opt out of non-essential systems
- Appeal decisions through dispute resolution

### Implementation

Citizen interactions are handled through [`routes/memory.py`](../routes/memory.py) (agent mode), [`routes/identity.py`](../routes/identity.py) (identity management), and the frontend components.

## Interaction Model

### Decision Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Citizen    │     │  Enterprise  │     │  Government  │
│   Proposes   │     │   Reviews    │     │   Approves   │
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                    ┌───────▼───────┐
                    │   Dharma      │
                    │   Veto Check  │
                    └───────┬───────┘
                            │
                    ┌───────▼───────┐
                    │   Execute     │
                    │   Action      │
                    └───────────────┘
```

### Approval Matrix

| Action | Citizen | Enterprise | Government | Dharma |
|--------|:-------:|:----------:|:----------:|:------:|
| Personal mode change | ✅ Sole | ❌ | ❌ | ✅ Check |
| Agent contract (5d) | ✅ Required | ✅ Required | ❌ | ✅ Check |
| Agent contract (15d) | ✅ Required | ✅ Required | ✅ Advisory | ✅ Check |
| Agent contract (30d) | ✅ Required | ✅ Required | ✅ Required | ✅ Check |
| Enterprise license | ❌ | ✅ Sole | ✅ Advisory | ✅ Check |
| Policy change | ✅ Advisory | ✅ Required | ✅ Required | ✅ Check |
| Emergency declaration | ✅ Notify | ✅ Notify | ✅ Sole | ✅ Check |
| Constitutional amendment | ✅ Referendum | ✅ Required | ✅ Required | ✅ Block |

## Stakeholder Coordinator

The Stakeholder Coordinator (`core/governance/stakeholder_coordinator.py`) orchestrates multi-stakeholder actions:

1. **Propose** — Any stakeholder proposes an action
2. **Route** — The coordinator determines which stakeholders must approve
3. **Collect** — Approvals are collected from required stakeholders
4. **Check** — Dharma Veto Engine validates the action
5. **Execute** — The action is executed if all conditions are met
6. **Log** — The action and decision are recorded in the audit log

## Escalation Path

When stakeholders cannot reach consensus:

1. **Level 1: Mediation** — Automated mediation with 48-hour timeline
2. **Level 2: Arbitration** — Dharma Veto Engine binding arbitration
3. **Level 3: Constitutional Council** — Emergency review by all stakeholders
4. **Level 4: Citizen Referendum** — Direct vote by all citizens

---

*API endpoints available at [`/api/governance/*`](../routes/governance.py), [`/api/enterprise/*`](../routes/enterprise.py), and [`/api/stakeholder/*`](../routes/stakeholder.py)*
