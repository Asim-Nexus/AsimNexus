# Consensus Protocol

> **Multi-stakeholder consensus and voting mechanisms for Digital Nepal**

## Overview

The AsimNexus consensus protocol enables multiple stakeholders (Citizens, Enterprises, Government) to reach agreement on system decisions. The protocol supports weighted voting, multi-round consensus, and automatic escalation.

## Voting Mechanisms

### Weighted Voting

Each stakeholder's vote is weighted according to their constitutional authority:

| Stakeholder | Base Weight | Notes |
|-------------|:-----------:|-------|
| Government | 51% | Fixed by constitution |
| Enterprise | 49% | Fixed by constitution |
| Citizen | 1 vote each | Direct democracy |

### Vote Types

| Type | Description | Threshold |
|------|-------------|:---------:|
| Simple Majority | >50% of weighted votes | >50% |
| Supermajority | >66% of weighted votes | >66% |
| Unanimous | 100% of required stakeholders | 100% |
| Citizen Referendum | >50% of citizen votes | >50% |
| Constitutional | Government 51% + Enterprise 49% + Citizen >50% | All three |

## Consensus Rounds

### Round Structure

Each consensus round follows this structure:

1. **Proposal** — An action is proposed with full details
2. **Voting Period** — Stakeholders cast votes (default: 48 hours)
3. **Tally** — Votes are counted and weighted
4. **Result** — Pass/Fail determination
5. **Execution** — If passed, the action is executed
6. **Logging** — The round is recorded in the audit log

### Round States

| State | Description |
|-------|-------------|
| `PENDING` | Round created, awaiting votes |
| `ACTIVE` | Voting in progress |
| `PASSED` | Threshold met, action approved |
| `FAILED` | Threshold not met |
| `OVERRIDDEN` | Decision overridden by higher authority |
| `ESCALATED` | Sent to higher-level review |
| `EXPIRED` | Voting period ended without decision |

### Multi-Round Consensus

For contentious decisions, the protocol supports multiple rounds:

1. **Round 1** — Standard weighted vote (48 hours)
2. **Round 2** — If Round 1 fails, modified proposal (24 hours)
3. **Round 3** — Final round with Dharma Engine mediation (12 hours)
4. **Escalation** — If all rounds fail, escalated to Constitutional Council

## Override Mechanisms

### Government Override

The Government can override consensus decisions in specific circumstances:

1. **National Security** — Threat to national security
2. **Emergency** — During declared emergency
3. **Constitutional Violation** — Decision violates constitution

Each override is:
- Logged with full justification
- Subject to post-hoc review within 7 days
- Automatically expires after 30 days
- Counted and limited (max 5 per quarter)

### Dharma Veto

The Dharma Veto Engine can override any decision that violates the 6 immutable rules:

1. Automatic — No human intervention required
2. Immediate — Veto is applied instantly
3. Irreversible — Cannot be overridden by any stakeholder
4. Transparent — Full explanation provided

## Clone Voting

### Multi-Clone Consensus

When multiple AI clones participate in decision-making:

1. Each clone casts an independent vote
2. Clone votes are aggregated by weighted average
3. Clone consensus is advisory (not binding)
4. Clone voting is used for:
   - Technical decisions
   - Resource allocation
   - Optimization proposals
   - Self-evolution decisions

### Clone Voting Interface

The clone voting UI is available at:
- [`frontend/src/components/consensus/CloneVotingCard.tsx`](../frontend/src/components/consensus/CloneVotingCard.tsx)
- [`frontend/src/components/identity/IdentityPanel.tsx`](../frontend/src/components/identity/IdentityPanel.tsx)

## API Endpoints

### Consensus V1

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/consensus/vote` | POST | Trigger a consensus vote |
| `/api/consensus/{round_id}/override` | POST | Override a consensus round |
| `/api/consensus/stats` | GET | Get consensus statistics |
| `/api/consensus/list` | GET | List consensus rounds |
| `/api/consensus/pending` | GET | Get pending consensus items |

### Consensus V2

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/consensus/vote` | POST | Cast a consensus vote (V2) |
| `/api/v1/consensus/weighted-vote` | POST | Cast a weighted consensus vote (V2) |
| `/api/v1/consensus/status` | GET | Get consensus V2 status |

### Dharma Engine

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dharma/status` | GET | Dharma engine status |
| `/api/dharma/veto` | POST | Check an action against Dharma Veto Engine |
| `/api/dharma/veto-check` | POST | Check action against Dharma veto rules |
| `/api/dharma/cultural-check` | POST | Check action against cultural compliance |
| `/api/dharma/veto-status` | GET | Get Dharma veto status |

## Implementation

The consensus protocol is implemented in:

- [`routes/consensus.py`](../routes/consensus.py) — API endpoints
- [`core/governance/stakeholder_coordinator.py`](../core/governance/stakeholder_coordinator.py) — Multi-stakeholder coordination
- [`core/dharma_chakra/veto_engine.py`](../core/dharma_chakra/veto_engine.py) — Dharma Veto Engine
- [`frontend/src/components/consensus/`](../frontend/src/components/consensus/) — Frontend components
