# AsimNexus AIOS — Intake (7 Questions)

> **Purpose:** Source of truth for your AsimNexus AIOS configuration.  
> **Filed by:** `/onboard` skill on first run.  
> **Updated:** When your context changes significantly.

---

## Q1: Who are you, what do you offer, and who is your ICP?

**Your Identity:**
```
Name/Role: [Your name and primary role]
Organization: [Company, community, or personal]
Location: [Country, region]
```

**What You Offer:**
```
Products/Services: [What you build, sell, or provide]
Value Proposition: [Why people choose you]
```

**Ideal Customer Profile (ICP):**
```
Who: [Demographic, role, industry]
Pain Point: [What problem you solve for them]
Scale: [Individual | Business | Government | Nation]
```

---

## Q2: What does your voice sound like? (Samples)

Provide 3-5 examples of your writing/speaking style:

```
Sample 1: [Professional email or announcement]
Sample 2: [Casual conversation or chat]
Sample 3: [Technical documentation or specification]
Sample 4: [Persuasive or sales-oriented]
Sample 5: [Crisis or urgent communication]
```

---

## Q3: What are your top priorities for the next 90 days?

| Priority | Goal | Deadline | Status |
|----------|------|----------|--------|
| P1 | [Critical: Must achieve] | [Date] | [Not started / In progress / At risk] |
| P2 | [Important: Should achieve] | [Date] | [Not started / In progress] |
| P3 | [Nice to have] | [Date] | [Backlog] |

**If only one thing ships in 90 days, what must it be?**
```
[Single most important outcome]
```

---

## Q4: How do you track revenue / value?

**Revenue Metrics** (if applicable):
```
Primary Revenue Stream: [Description]
Secondary Streams: [List]
Tracking Method: [Tool / dashboard / manual]
Target (monthly): [Amount or goal]
```

**Value Metrics** (for non-commercial):
```
Impact Metric: [What you measure]
Current Value: [Baseline]
Target: [Goal]
Tracking: [How you measure]
```

---

## Q5: What communication channels do you use?

| Channel | Purpose | Frequency | Integration |
|---------|---------|-----------|-------------|
| Email | [Primary/secondary] | [Daily/weekly] | [`connectors/google_ecosystem.py`](connectors/google_ecosystem.py) |
| Calendar | [Scheduling] | [Daily] | [`connectors/google_ecosystem.py`](connectors/google_ecosystem.py) |
| Chat/Messaging | [Internal/external] | [Continuous] | [`connectors/unified_messaging_connector.py`](connectors/unified_messaging_connector.py) |
| File Storage | [Documents/assets] | [On-demand] | `storage/` |
| Mesh Peers | [Federation sync] | [Event-driven] | [`mesh/offline_sync_engine.py`](mesh/offline_sync_engine.py) |

---

## Q6: Where do you store documents and data?

| Data Type | Location | Backup | Sensitivity |
|-----------|----------|--------|-------------|
| Personal Files | `storage/` | [Yes/No] | [Public/Internal/Confidential/Sovereign] |
| Business Docs | `storage/` | [Yes/No] | [Public/Internal/Confidential/Sovereign] |
| Contracts | `core/contracts/` | [Yes/No] | [Confidential/Sovereign] |
| Financial Records | `core/finance/` | [Yes/No] | [Confidential/Sovereign] |
| Government/Identity | `core/government/` | [Yes/No] | [Sovereign] |

**Mesh Replication Policy:**
```
[ ] Never replicate sovereign data
[ ] Replicate encrypted only
[ ] Replicate with consent only
[ ] Full mesh replication
```

---

## Q7: What is your biggest time-suck right now?

```
Description: [What takes too much of your time]
Current Effort: [Hours per week]
Manual/Automatable: [Is this repetitive?]
Desired Outcome: [What would free you up to do?]
Priority to Automate: [1-5, where 1 = highest]
```

---

## ✅ Intake Complete

Once all 7 questions are answered, run `/onboard` scaffold to generate:
- [`context/about-me.md`](context/about-me.md) — Personal identity and voice
- [`context/about-business.md`](context/about-business.md) — Business context and ICP
- [`context/priorities.md`](context/priorities.md) — 90-day priorities
- [`connections.md`](connections.md) — Connection registry
