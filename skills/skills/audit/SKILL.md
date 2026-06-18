# /audit — AsimNexus Constitutional Weekly Audit

> **Purpose:** Score your AIOS across the Four Cs (25 pts each = 100 total), identify gaps, plan fixes.  
> **Frequency:** Weekly (every Monday recommended).  
> **Trigger:** `/audit` command.

---

## Scoring Framework

Each of the Four Cs is scored 0-25 based on **coverage**, **reliability**, **veto compliance**, and **documentation**.

| Score | Meaning |
|-------|---------|
| 0-5 | Missing — not implemented or non-functional |
| 6-10 | Concept — defined but not wired |
| 11-15 | Partial — works but has known gaps |
| 16-20 | Real — production-grade, documented |
| 21-25 | Excellent — hardened, monitored, redundant |

---

## C1: Context Audit (0-25)

**What to check:**

| Item | Max | Score | Notes |
|------|-----|-------|-------|
| [`context/about-me.md`](../../../context/about-me.md) is current | 4 | | |
| [`context/about-business.md`](../../../context/about-business.md) is current | 4 | | |
| [`context/priorities.md`](../../../context/priorities.md) is current | 4 | | |
| [`aios-intake.md`](../../../aios-intake.md) reflects reality | 4 | | |
| [`references/constitution.md`](../../../references/constitution.md) up to date | 3 | | |
| [`references/4cs-framework.md`](../../../references/4cs-framework.md) accurate | 3 | | |
| Voice/style guide is consistent | 3 | | |

**Context Score:** ___ / 25

**Gap:** [What's missing or outdated]

---

## C2: Connections Audit (0-25)

**What to check (7 Tier-1 Domains):**

| Domain | Status | Reliability | Veto Wired | Score (0-4) |
|--------|--------|-------------|------------|-------------|
| Email | | | | |
| Calendar | | | | |
| Files / Documents | | | | |
| Chat / Messaging | | | | |
| Payment / Finance | | | | |
| Government / Identity | | | | |
| Mesh / Peers | | | | |

**Connection Score:** ___ / 25 (sum ÷ 7 × 25)

**Gap:** [Which connection is weakest — fix it first]

---

## C3: Capabilities Audit (0-25)

**What to check:**

| Capability | Works? | Veto Gate? | Audit Trail? | Score (0-5) |
|-----------|--------|------------|-------------|-------------|
| Chat / Assistant | | | | |
| Agent Runner | | | | |
| Tool Execution | | | | |
| Contract Workflow | | | | |
| MCP Tool Calls | | | | |

**Capabilities Score:** ___ / 25

**Gap:** [Which capability needs most work]

---

## C4: Cadence Audit (0-25)

**What to check:**

| Beat | Running? | Reliable? | Monitored? | Score (0-5) |
|------|----------|-----------|------------|-------------|
| Dreaming Cycle | | | | |
| Mesh Sync | | | | |
| ΔT Engine | | | | |
| Audit Flush | | | | |
| Level-3 Confirm | | | | |

**Cadence Score:** ___ / 25

**Gap:** [Which beat is weakest]

---

## Overall Score

| C | Score | Weight | Weighted |
|---|-------|--------|----------|
| Context | ___ | ×1 | ___ |
| Connections | ___ | ×1 | ___ |
| Capabilities | ___ | ×1 | ___ |
| Cadence | ___ | ×1 | ___ |
| **Total** | | | **___ / 100** |

---

## Leverage-Weighted Gap Ranking

Rank gaps by impact × effort:

| Rank | Gap | Impact (1-10) | Effort (1-10) | Leverage Score (I÷E) |
|------|-----|---------------|---------------|---------------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

**Fix the highest leverage item first.**

---

## Action Items

1. [Highest leverage fix from above]
2. [Second priority]
3. [Third priority]

---

## Previous Score

Last week: ___ / 100  
This week: ___ / 100  
Change: ___  

**Trend:** 📈 Improving / 📉 Declining / ➡️ Stable
