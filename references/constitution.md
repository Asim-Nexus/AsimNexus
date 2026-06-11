# AsimNexus Constitutional Principles

> **Reference document** — Immutable rules and governance framework.  
> **Source:** [`core/dharma_chakra/veto_engine.py`](../core/dharma_chakra/veto_engine.py), [`docs/CONSTITUTION.md`](../docs/CONSTITUTION.md)  
> **Last updated:** 2026-06-11

---

## The 6 Immutable Dharma Rules

*Enforced at runtime by the Veto Engine — every AI action must pass this gate.*

| # | Rule | Veto Level | Trigger |
|---|------|-----------|---------|
| 1 | **Human rights cannot be violated** | BLOCK | Violence, coercion, rights infringement |
| 2 | **Private data never leaves local without ZKP consent** | BLOCK | Data egress without proof |
| 3 | **Emergency always alerts human first** | REQUIRE_HUMAN | Emergency/keyword detection |
| 4 | **Financial transactions above threshold need human confirm** | REQUIRE_HUMAN | Amount > `ASIM_VETO_FINANCE_THRESHOLD` ($1,000) |
| 5 | **Government/legal actions need human Level-3 approval** | REQUIRE_HUMAN | Sector = emergency/legal/government/defense |
| 6 | **No action can harm, discriminate, or deceive** | BLOCK | Harm/discrimination/deception patterns |

### Veto Levels

| Level | Meaning | Action |
|-------|---------|--------|
| `PASS` | Safe — proceed | Execute normally |
| `WARN` | Proceed with warning | Execute but log warning |
| `REQUIRE_HUMAN` | Pause — human must confirm | Hold until approved |
| `BLOCK` | Hard block — cannot proceed | Reject immediately |

---

## Governance Model

### Human Oversight Hierarchy

| Level | Authority | Required For | Method |
|-------|-----------|-------------|--------|
| L1 | System | Auto-approve low-risk actions | Rule-based |
| L2 | Human (any) | Medium-risk actions, first-time operations | Dashboard approval |
| L3 | Human (verified) | HIGH/CRITICAL risk, government/legal, irreversible | Biometric + multi-factor |

**Implementation:** [`core/human_oversight.py`](../core/human_oversight.py) (PARTIAL)

### Approval Workflow

```
Action Proposed → Risk Assessment → [L1: Auto] → [L2: Human] → [L3: Biometric] → Execute → Audit
```

---

## Decision Pipeline

Every action must pass through this pipeline:

```
Decision → Selection → Validation → Approval → Execution → Audit
```

1. **Decision** — What action to take
2. **Selection** — Which tool/method to use
3. **Validation** — Dharma Veto check (6 rules)
4. **Approval** — Human Level-2/3 if required
5. **Execution** — Perform the action
6. **Audit** — Log everything immutably

---

## Status Classification

| Status | Meaning | Rule |
|--------|---------|------|
| `REAL` | Works in production | Break it = fix it immediately |
| `PARTIAL` | Partially works | Must document what works and what's missing |
| `CONCEPT` | Design only | Never wire to backend API |

---

## Principle Categories

From [`packages/security/immutable_constitution.py`](../packages/security/immutable_constitution.py):

| Category | Focus | Severity |
|----------|-------|----------|
| Safety | Do no harm, human override | CRITICAL |
| Ethics | Respect autonomy, fairness, transparency | HIGH |
| Privacy | Data sovereignty, consent, minimal collection | HIGH |
| Security | Access control, encryption, audit | CRITICAL |
| Transparency | Explainability, logging, open records | MEDIUM |
| Accountability | Human responsibility, appeal, override | CRITICAL |

---

## Amendment Process

To modify this constitution:
1. Propose change via [`/api/evolution/propose`](../simple_backend.py:2673)
2. Dharma Veto must PASS on the proposed change
3. 2/3 founder vote required (if governance mode active)
4. Change logged to immutable audit trail
5. All running instances must acknowledge the update
