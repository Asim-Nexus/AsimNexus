# /onboard — AsimNexus AIOS First-Run Setup

> **Purpose:** Day 1 onboarding — fill the 7-question intake, scaffold context files, establish your constitutional AIOS.  
> **Trigger:** First run after `CLAUDE.md` is created, or `/onboard` command.  
> **Duration:** ~15 minutes.

---

## Phase 1: Open the Intake

1. Open [`aios-intake.md`](../../../aios-intake.md)
2. Answer all 7 questions honestly:
   - **Q1:** Identity, offer, ICP
   - **Q2:** Voice samples (provide 3-5)
   - **Q3:** Top 3 priorities for next 90 days
   - **Q4:** Revenue/value tracking method
   - **Q5:** Communication channels you use
   - **Q6:** Document/data storage locations
   - **Q7:** Biggest time-suck right now
3. Save the file

---

## Phase 2: Scaffold Context Files

Based on Q1-Q3 answers, scaffold:

### [`context/about-me.md`](../../../context/about-me.md)
```
# About Me

## Identity
[Name, role, organization, location from Q1]

## Voice & Style
[Voice samples from Q2 — distilled into communication style guide]
- Tone: [Professional / Casual / Technical / Persuasive]
- Formality: [High / Medium / Low]
- Language: [Primary language(s)]

## Values
[What matters to you — derived from Q1 and overall context]
```

### [`context/about-business.md`](../../../context/about-business.md)
```
# About My Business / Organization

## What I Do
[Offer and value proposition from Q1]

## ICP
[Ideal Customer Profile from Q1]

## Revenue / Value Model
[From Q4]

## Communication Channels
[From Q5]
```

### [`context/priorities.md`](../../../context/priorities.md)
```
# Current Priorities

## 90-Day Goals (from Q3)
| Priority | Goal | Deadline | Status |
|----------|------|----------|--------|
| P1 | [Critical] | [Date] | [Status] |
| P2 | [Important] | [Date] | [Status] |
| P3 | [Nice to have] | [Date] | [Status] |

## This Week's Focus
[Single most important thing to ship this week]

## Blockers
[What's blocking progress right now]
```

---

## Phase 3: Initialize Connections

Based on Q5-Q6 answers:

1. Open [`connections.md`](../../../connections.md)
2. Verify each of the 7 Tier-1 domains reflects your actual setup
3. For each domain:
   - Mark ✅ REAL if adapter is wired and working
   - Mark ⚠️ PARTIAL if needs configuration
   - Leave blank if not yet connected

---

## Phase 4: Dharma Veto Verification

1. Start the backend: `python simple_backend.py`
2. Verify veto engine is active:

```bash
curl http://localhost:8000/api/dharma/veto-status
```

Expect response: `{"status": "active", "rules_enforced": 6, ...}`

3. Test a veto check:

```bash
curl -X POST http://localhost:8000/api/dharma/veto-check \
  -H "Content-Type: application/json" \
  -d '{"action": "send_email", "content": "Hello, how are you?", "context": {"sector": "personal"}}'
```

---

## Phase 5: Close-out

**After completing all phases:**

```
✅ Intake answered (aios-intake.md)
✅ Context files scaffolded (context/about-me.md, about-business.md, priorities.md)
✅ Connections verified (connections.md)
✅ Dharma Veto confirmed active
```

**Then ask me:**
> *"Based on my intake and context, what should I focus on this week to ship my first automation?"*
