# Smart Contract Law

> **Legal framework for 5/15/30 day AI agent contracts**

## Preamble

This document defines the legal framework for time-bound, scope-bounded AI agent contracts within the AsimNexus ecosystem. All AI agents operating on behalf of humans must operate under a valid contract that specifies duration, scope, and terms.

## Article I: Contract Fundamentals

### Section 1: Contract Duration

Agent contracts are available in three durations:

| Duration | Max Scope | Renewal Limit | Cooling-Off |
|----------|:---------:|:-------------:|:-----------:|
| **5 Days** | Limited | Unlimited | None |
| **15 Days** | Standard | 3 consecutive | 2 days |
| **30 Days** | Full | 1 consecutive | 7 days |

### Section 2: Contract Scope

Every contract must define:

1. **Permitted Actions** — What the agent CAN do
2. **Prohibited Actions** — What the agent CANNOT do
3. **Data Access Level** — What data the agent can access
4. **Resource Limits** — Computational and API rate limits
5. **Human Oversight** — Which actions require human approval

### Section 3: Data Access Levels

| Level | Description | Examples |
|-------|-------------|----------|
| `NONE` | No data access | Public information only |
| `READ_ONLY` | Read access only | View messages, read files |
| `READ_WRITE` | Read and write | Send messages, create files |
| `ADMIN` | Full access | Manage settings, modify system |

## Article II: Contract Lifecycle

### Section 1: Proposal

1. A human (Citizen or Enterprise) proposes a contract
2. The proposal specifies duration, scope, and terms
3. The system validates the proposal against constitutional rules
4. The proposed contract is hashed and timestamped

### Section 2: Signing

1. The human signs the contract (digital signature)
2. The agent cryptographically binds to the contract
3. The contract is recorded in the immutable audit log
4. The agent begins operation under the contract terms

### Section 3: Execution

1. The agent operates within the defined scope
2. All actions are logged and auditable
3. The human can monitor agent activity in real-time
4. The human can revoke authority at any time

### Section 4: Expiry

1. Contracts automatically expire after their duration
2. Expired contracts enter a grace period (24 hours)
3. During grace period, the agent can only complete pending tasks
4. After grace period, all agent authority is revoked

### Section 5: Renewal

1. Contracts can be renewed before expiry
2. Renewal requires fresh human consent
3. Consecutive renewals are limited (see Article I, Section 1)
4. Cooling-off periods apply after maximum renewals

### Section 6: Revocation

1. Humans can revoke contracts at any time
2. Revocation is immediate and irreversible
3. The agent must cease all operations within 60 seconds
4. A revocation audit is automatically generated

## Article III: Agent Binding

### Section 1: Cryptographic Binding

Each contract creates a cryptographic binding between:

- **Human Identity** — Verified through biometric or digital signature
- **Agent Identity** — Unique agent ID with public key
- **Contract Terms** — Hashed and signed contract document

### Section 2: Identity Verification

1. Human identity must be verified before contract signing
2. Agent identity must be registered in the system
3. Both parties' signatures are recorded in the contract

## Article IV: Compliance and Auditing

### Section 1: Action Permissions

Every agent action is checked against the contract:

```python
def check_action_permitted(contract, action):
    """Check if an action is permitted under the contract."""
    if contract.is_expired():
        return False, "Contract expired"
    if action in contract.scope.prohibited_actions:
        return False, "Action prohibited by contract"
    if action not in contract.scope.permitted_actions:
        return False, "Action not in permitted scope"
    return True, "Action permitted"
```

### Section 2: Audit Trail

1. Every contract lifecycle event is logged
2. Every agent action is recorded with timestamp
3. Audit logs are immutable and append-only
4. Humans can view their contract audit trail at any time

### Section 3: Compliance Scoring

Each contract receives a compliance score based on:

- Adherence to scope (40%)
- Data access compliance (30%)
- Resource usage limits (20%)
- Human satisfaction rating (10%)

## Article V: Dispute Resolution

### Section 1: Human Complaints

1. Humans can file complaints about agent behavior
2. Complaints are investigated within 24 hours
3. Violations result in immediate contract suspension
4. Repeated violations result in agent blacklisting

### Section 2: Agent Appeals

1. Agents can appeal human revocation decisions
2. Appeals are reviewed by the Dharma Veto Engine
3. Appeals must demonstrate constitutional violation
4. Successful appeals restore agent authority

## Article VI: Special Provisions

### Section 1: Emergency Contracts

During declared emergencies:
1. Contract durations can be shortened (minimum 1 day)
2. Scope can be expanded for emergency response
3. Cooling-off periods are suspended
4. All emergency contracts are reviewed post-emergency

### Section 2: Enterprise Agent Pools

Enterprises can maintain agent pools:
1. Pool contracts cover multiple agents under one agreement
2. Individual agents are bound by sub-contracts
3. The enterprise is liable for all pool agent actions
4. Pool contracts have stricter audit requirements

---

*Contract system implemented in [`core/agent_contract.py`](../core/agent_contract.py)*
