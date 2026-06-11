# The Four Cs of an AIOS™ — AsimNexus Edition

> **Reference document** — Adapted from Nate Herk's AIS-OS Framework  
> **Original:** [github.com/nateherkai/AIS-OS](https://github.com/nateherkai/AIS-OS)  
> **AsimNexus Adaptation:** Constitutional + Sovereign + Mesh-Connected  
> **Last updated:** 2026-06-11

---

## Overview

An AI Operating System (AIOS) has four structural pillars: **Context**, **Connections**, **Capabilities**, and **Cadence**. In AsimNexus, each pillar is reinforced by the Dharma Constitution — the Veto Engine, Human Oversight, and Immutable Audit Trail.

```
┌─────────────────────────────────────────────────────┐
│                   CONSTITUTION                       │
│  (Veto Engine · Human Oversight · Immutable Audit)   │
├──────────┬──────────┬──────────┬─────────────────────┤
│ CONTEXT  │CONNECTIONS│CAPABILITIES│     CADENCE       │
│ Knows    │ Reaches  │ Does Work │ Runs on Schedule   │
│ Who/What │ Data/Svc │ Via Agents│ + Events           │
└──────────┴──────────┴──────────┴─────────────────────┘
         Every action passes through Dharma Veto
```

---

## C1: Context — Dharma Context

*Knows who you are, what you do, and what rules govern you.*

### Components

| Component | File | Purpose |
|-----------|------|---------|
| Personal Identity | [`context/about-me.md`](../context/about-me.md) | Who you are, voice, values |
| Business Context | [`context/about-business.md`](../context/about-business.md) | What you do, ICP, revenue |
| Priorities | [`context/priorities.md`](../context/priorities.md) | 90-day goals, weekly focus |
| Intake | [`aios-intake.md`](../aios-intake.md) | 7-question source of truth |
| Constitution | [`references/constitution.md`](../references/constitution.md) | Immutable rules |
| Operating Manual | [`CLAUDE.md`](../CLAUDE.md) | Root AIOS manual |

### AsimNexus Difference
- Context is **constitutionally grounded** — every piece of context must comply with Dharma rules
- **Sovereign by default** — personal context never leaves device without consent
- **Mesh-aware** — context can be selectively shared with mesh peers via consent

### Score Criteria (0-25)
- Are all context files populated and current?
- Does the AIOS accurately represent who you are and what you do?
- Is voice/style consistent across all communications?
- Are priorities actionable and up-to-date?

---

## C2: Connections — Mesh Connections

*Reaches every data source, service, and peer — on-device and across the mesh.*

### The 7 Tier-1 Domains

| # | Domain | AsimNexus Adapter | Constitutional Gate |
|---|--------|-------------------|---------------------|
| 1 | Email | [`connectors/google_ecosystem.py`](../connectors/google_ecosystem.py) | Veto before send |
| 2 | Calendar | [`connectors/google_ecosystem.py`](../connectors/google_ecosystem.py) | Confirm before modify |
| 3 | Files | `storage/` | Veto before delete |
| 4 | Chat | [`connectors/unified_messaging_connector.py`](../connectors/unified_messaging_connector.py) | Anti-impersonation check |
| 5 | Finance | [`connectors/nepal_banking.py`](../connectors/nepal_banking.py), [`core/finance/`](../core/finance/) | Threshold veto + audit |
| 6 | Government | [`core/government/`](../core/government/) | Level-3 human required |
| 7 | Mesh Peers | [`mesh/offline_sync_engine.py`](../mesh/offline_sync_engine.py) | Consent + air-gap |

### AsimNexus Difference
- **Offline-first** — mesh sync works without internet (CRDT-based)
- **Air-gap mode** — full isolation from internet when needed
- **Federated consent** — peers must consent before data sharing
- **ZKP privacy** — share proofs, not data

### Score Criteria (0-25)
- How many of the 7 domains are connected and working?
- How reliable are the connections?
- Are all connections wired through the Dharma Veto?
- Is mesh sync working and verified?

---

## C3: Capabilities — Constitutional Capabilities

*Does work through agents that check every action against the Dharma Veto.*

### The Capability Stack

```
┌──────────────────────────────────┐
│         User Interface           │  Frontend Dashboard / Chat
├──────────────────────────────────┤
│         Agent Runner             │  /api/agent/run
├──────────────────────────────────┤
│       Tool Execution             │  /api/tools/execute
├──────────────────────────────────┤
│      ┌──────────────────┐        │
│      │  Dharma Veto     │        │  Every action checked here
│      │  Gate ❖          │        │
│      └──────────────────┘        │
├──────────────────────────────────┤
│  MCP  │ Contracts │ Brain        │  Specialized capabilities
└──────────────────────────────────┘
```

### Key Capabilities

| Capability | Entry Point | Veto Gate | Audit |
|-----------|-------------|-----------|-------|
| Chat / Assistant | [`/chat`](../simple_backend.py:980) | ✅ Inline | ✅ |
| Agent Runner | [`/api/agent/run`](../simple_backend.py:3257) | ✅ Before execution | ✅ |
| Tools | [`/api/tools/execute`](../simple_backend.py:3353) | ✅ Veto check | ✅ |
| Contracts | [`/api/contracts/`](../simple_backend.py:1516) | ✅ Gate-2 | ✅ |
| MCP | [`/api/mcp/call`](../simple_backend.py:3151) | ✅ Approval queue | ✅ |
| Brain | [`/api/brain/process`](../simple_backend.py:1181) | ✅ Dharma inline | ✅ |

### AsimNexus Difference
- **Every capability has a constitutional gate** — no action bypasses Dharma
- **Human-in-the-loop for high-risk** — Level-3 biometric confirmation
- **Capability discovery via DHT** — mesh peers can discover and offer capabilities

### Score Criteria (0-25)
- Do all capabilities work reliably?
- Is every capability wired through the Dharma Veto?
- Is there an audit trail for every capability execution?
- Are capabilities documented and discoverable?

---

## C4: Cadence — Sovereign Cadence

*Runs on schedule, on events, and on human command — autonomously but accountably.*

### Cadence Beats

| Beat | Engine | Frequency | Human Oversight |
|------|--------|-----------|-----------------|
| Dreaming | [`delta_t_engine.py`](../core/dharma/delta_t_engine.py) | Continuous background | None (read-only) |
| Mesh Sync | [`offline_sync_engine.py`](../mesh/offline_sync_engine.py) | On-connect + periodic | Consent-based |
| ΔT Analysis | [`delta_t_engine.py`](../core/dharma/delta_t_engine.py) | Per-transaction | Alert on threshold |
| Audit Flush | [`audit_logger.py`](../core/security/audit_logger.py) | On threshold | Review on demand |
| Level-3 Confirm | [`level3_confirmation.py`](../core/security/level3_confirmation.py) | On HIGH/CRITICAL | Biometric required |
| Weekly Audit | `/audit` skill | Every Monday | Human-led |
| Weekly Ship | `/level-up` skill | Weekly | Human-led |

### AsimNexus Difference
- **Cadence respects sovereignty** — no phone-home, no cloud dependency
- **Offline-capable** — all beats work without internet
- **Human-gated** — no autonomous action can bypass human oversight for critical operations

### Score Criteria (0-25)
- Are all cadence beats running reliably?
- Is monitoring in place for each beat?
- Are beats constitutionally gated where needed?
- Is there a recovery mechanism for failed beats?

---

## The Three Ms of AI™ (for /level-up)

The Three Ms framework guides weekly automation development:

| M | Focus | Question |
|---|-------|----------|
| **Mindset** | Find the candidate | What repetitive task can be eliminated or automated? |
| **Method** | Scope the automation | What's the input → process → output pipeline? |
| **Machine** | Build it | How do we implement with veto, audit, and tests? |

### EAD Framework

| Action | When | Example |
|--------|------|---------|
| **E**liminate | If breaking nothing, don't build | Stop a redundant report |
| **A**utomate | If repetitive + rule-based | Auto-send weekly invoice |
| **D**elegate | If needs human judgment | Escalate complex cases to human |

---

## Scoring Summary

| C | Domain | Max | Your Score | Target |
|---|--------|-----|-----------|--------|
| C1 | Context | 25 | | 20+ |
| C2 | Connections | 25 | | 20+ |
| C3 | Capabilities | 25 | | 20+ |
| C4 | Cadence | 25 | | 20+ |
| **Total** | | **100** | | **80+** |

**Use the `/audit` skill weekly to score and track improvement.**

---

## The Bike Method — Progression Phases

| Phase | Weeks | Trust Level | Automation Style | Human Oversight |
|-------|-------|-------------|-----------------|-----------------|
| 1 — Training Wheels | 1-2 | Low | Simple, supervised | Heavy (L2 every action) |
| 2 — Confident | 3-4 | Medium | Moderate complexity | Standard (L2 exceptions) |
| 3 — Trust | 5-8 | High | Complex pipelines | Reduced (L3 only) |
| 4 — Autopilot | 9+ | Full | Autonomous within bounds | Exception-only |

---

*This document is updated when the framework evolves. Use `/audit` to track alignment.*
