# Dharma Chakra — The 6 Immutable Rules

> **The constitutional veto engine that protects Digital Nepal from tyranny**

## Overview

The Dharma Chakra (धर्म चक्र — "Wheel of Dharma") is the constitutional veto engine of AsimNexus. It enforces 6 immutable rules that **cannot be overridden by any stakeholder**, including the Government, Enterprises, or even a unanimous vote. These rules are the digital equivalent of fundamental constitutional rights — they exist to prevent the system from being subverted.

## The 6 Immutable Rules

### Rule 1: No Absolute Power

**No single entity or coalition can hold more than 51% of total system authority.**

- Government is capped at 51%
- Enterprise is capped at 49%
- No supermajority can override this rule
- Any attempt to concentrate power is automatically vetoed

**Enforcement**: The system continuously monitors power distribution. If any entity attempts to exceed their cap, the Dharma Engine immediately blocks the action and triggers an alert.

### Rule 2: Citizen Sovereignty

**Citizen data rights are inviolable and cannot be waived, transferred, or overridden.**

- Citizens always own their data
- No contract can waive data rights
- No emergency can suspend data sovereignty
- Data access requires explicit, revocable consent

**Enforcement**: Any action that would violate citizen data sovereignty is automatically blocked. This includes government surveillance orders, enterprise data requests, and even citizen agreements that would waive these rights.

### Rule 3: Contract Integrity

**All agent contracts must be honored according to their terms.**

- Contracts are immutable once signed
- Terms cannot be changed unilaterally
- Early termination requires mutual consent
- Contract violations result in automatic penalties

**Enforcement**: The system enforces contract terms programmatically. If an agent violates contract terms, its authority is immediately revoked. If a human violates contract terms, the agent is released from obligations.

### Rule 4: Audit Transparency

**All system actions must be auditable by authorized parties.**

- Every action is logged with timestamp and identity
- Audit logs are append-only and immutable
- Citizens can audit actions affecting their data
- Government has audit access for compliance
- Audit logs cannot be deleted or modified

**Enforcement**: Any action that is not properly logged is treated as if it never happened. Attempts to modify or delete audit logs trigger immediate security alerts and potential hard-lock activation.

### Rule 5: Emergency Sunset

**Emergency powers automatically expire after 30 days unless ratified through the standard process.**

- Emergency declarations are temporary by design
- Automatic sunset at 30 days
- Extension requires full constitutional process
- No consecutive emergency declarations for the same issue

**Enforcement**: The system automatically revokes emergency powers at the 30-day mark. If the same emergency is re-declared, the Dharma Engine blocks it and escalates to the Constitutional Council.

### Rule 6: Constitutional Supremacy

**The constitution is the supreme law of the system — no action can violate constitutional principles.**

- All actions are checked against the constitution
- Constitutional violations are automatically vetoed
- No amendment can violate the 6 immutable rules
- The Dharma Engine is the final interpreter

**Enforcement**: Every action is checked against all constitutional rules before execution. If any rule is violated, the action is blocked with a detailed explanation of which rule was violated and why.

## How the Veto Engine Works

### Check Flow

```
Action Proposed
    │
    ▼
┌─────────────────┐
│ Rule 1: Power   │── No absolute power violation?
│ Balance Check   │
└────────┬────────┘
         │ Pass
         ▼
┌─────────────────┐
│ Rule 2: Citizen │── Citizen sovereignty respected?
│ Sovereignty     │
└────────┬────────┘
         │ Pass
         ▼
┌─────────────────┐
│ Rule 3: Contract│── Contract integrity maintained?
│ Integrity       │
└────────┬────────┘
         │ Pass
         ▼
┌─────────────────┐
│ Rule 4: Audit   │── Proper audit trail?
│ Transparency    │
└────────┬────────┘
         │ Pass
         ▼
┌─────────────────┐
│ Rule 5: Sunset  │── Emergency powers within limits?
│ Emergency       │
└────────┬────────┘
         │ Pass
         ▼
┌─────────────────┐
│ Rule 6: Const.  │── Constitutional compliance?
│ Supremacy       │
└────────┬────────┘
         │ Pass
         ▼
    Action Approved ✅
```

### Veto Response

When an action is vetoed, the engine returns:

```json
{
    "vetoed": true,
    "rule_violated": "Rule 1: No Absolute Power",
    "reason": "Proposed action would grant Government 60% authority, exceeding the 51% constitutional cap",
    "details": {
        "current_balance": {"government": 51, "enterprise": 49},
        "proposed_balance": {"government": 60, "enterprise": 40},
        "violation": "government_power_exceeds_51_percent"
    },
    "timestamp": "2025-01-15T10:30:00Z",
    "veto_id": "veto_abc123"
}
```

## Emergency Override Protocol

In genuine existential threats to the system:

1. **Constitutional Council** (all stakeholders) can vote to temporarily suspend a rule
2. Requires **100% unanimous vote** of all stakeholders
3. Suspension is limited to **24 hours**
4. Full review and ratification required within **7 days**
5. Any abuse triggers **automatic hard-lock** of the system

## Implementation

The Dharma Chakra is implemented in:

- [`core/dharma_chakra/veto_engine.py`](../core/dharma_chakra/veto_engine.py) — Core veto engine with the 6 rules
- [`routes/consensus.py`](../routes/consensus.py) — API endpoints for dharma checks
- [`core/governance/stakeholder_coordinator.py`](../core/governance/stakeholder_coordinator.py) — Multi-stakeholder consensus integration

---

*"The Dharma Chakra turns, but it never breaks."*
