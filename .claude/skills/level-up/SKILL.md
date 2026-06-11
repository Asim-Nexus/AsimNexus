# /level-up — Weekly Automation Ship

> **Purpose:** Ship one real automation per week using the Three Ms of AI™ framework.  
> **Frequency:** Weekly.  
> **Trigger:** `/level-up` command.  
> **Goal:** One working, veto-gated, audited automation by end of session.

---

## Phase 1: Mindset — Find the Candidate

Interview yourself (or your user) with these questions:

### 1. What did you do last week that felt repetitive?
```
[Describe a task you did 3+ times]
```

### 2. What takes <30 minutes but happens daily?
```
[Small but frequent task]
```

### 3. What's the one thing you'd automate first if you could?
```
[Your dream automation]
```

### 4. Apply the EAD Framework
| Action | Description |
|--------|-------------|
| **E**liminate | If it breaks nothing, don't automate |
| **A**utomate | If it's repetitive + rule-based, automate it |
| **D**elegate | If it needs human judgment, delegate to human |

**Chosen Candidate:** [What you'll automate this week]

---

## Phase 2: Method — Scope the Automation

### 5-Step Pipeline

**Step 1 — Define Input**
```
What triggers this automation?
[ ] Message received
[ ] Schedule (cron)
[ ] File change
[ ] Manual trigger
[ ] Event from another system
```

**Step 2 — Define Process**
```
What steps does it perform?
1. 
2. 
3. 
```

**Step 3 — Define Output**
```
What does it produce?
[ ] Email/Send message
[ ] File/Report
[ ] Database update
[ ] API call
[ ] Mesh broadcast
```

**Step 4 — Define Veto Gates**
```
Which Dharma rules apply?
[ ] Rule 1: Human rights
[ ] Rule 2: Data sovereignty / ZKP
[ ] Rule 3: Emergency alert
[ ] Rule 4: Financial threshold
[ ] Rule 5: Government/legal Level-3
[ ] Rule 6: No harm/discrimination/deception

Human approval needed? [Yes/No — if Yes, Level: 1/2/3]
```

**Step 5 — Define Audit Requirements**
```
What to log:
- Action type: [READ/WRITE/DELETE/EXECUTE]
- Resource: [What is acted upon]
- User: [Who/system triggered it]
- Details: [What happened]
```

---

## Phase 3: Machine — Build It

### Boring-is-Beautiful Defaults

1. **Use existing patterns** — Follow the code style in [`simple_backend.py`](../../../simple_backend.py)
2. **Wire to veto** — Add Dharma check via [`/api/dharma/veto-check`](../../../simple_backend.py:1758)
3. **Add audit** — Log via [`core/security/audit_logger.py`](../../../core/security/audit_logger.py)
4. **Write a test** — Add to `tests/real/`
5. **Document** — Add endpoint to [`CLAUDE.md`](../../../CLAUDE.md)

### Automation Implementation Checklist

```
[ ] Code written
[ ] Veto gate integrated
[ ] Audit log added
[ ] Test written
[ ] Connection registered (if new)
[ ] CLAUDE.md updated (if new endpoint)
[ ] Human approval flow defined (if needed)
```

---

## Phase 4: Ship

1. Run the test:

```bash
pytest tests/real/test_your_automation.py -v
```

2. Test the endpoint:

```bash
curl http://localhost:8000/api/your-endpoint
```

3. Commit:

```bash
git add .
git commit -m "feat: [automation name] — weekly ship from /level-up"
```

---

## Weekly Tracking

| Week | Automation | Status | Veto Gated | Human Approval | Score Impact |
|------|-----------|--------|------------|----------------|-------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |

**4-Phase Progression:**
- **Phase 1** (Weeks 1-2): Training wheels — simple automations, heavy supervision
- **Phase 2** (Weeks 3-4): Confident — medium complexity, standard gates
- **Phase 3** (Weeks 5-8): Trust — complex automations, reduced oversight
- **Phase 4** (Week 9+): Autopilot — autonomous within constitutional bounds
