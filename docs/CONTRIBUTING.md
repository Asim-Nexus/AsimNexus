# Contributing to AsimNexus — Labeling Rules

> **tl;dr:** Every file MUST have a STATUS header. No exceptions.

## The Three Labels

### REAL
- Code works, tested, wired to backend
- Has `tests/real/test_<file>.py` with passing tests
- Backend endpoint returns live data (if applicable)
- No simulation stubs in critical path

### PARTIAL
- Framework/skeleton exists
- Some logic works, some is simulation
- Has `tests/prototype/` or `tests/integration/` tests
- Document what's missing in the STATUS line

### CONCEPT
- Design doc, placeholder, or vision only
- No working code (or only data structures)
- No backend endpoint
- Stored in `docs/vision/` or `core/concept/`

## File Header Template

```python
"""
STATUS: REAL — <one-line description of what actually works>

<rest of docstring>
"""
```

```python
"""
STATUS: PARTIAL — <what works> ; <what's missing>

<rest of docstring>
"""
```

```python
"""
STATUS: CONCEPT — <what this would be in the future>

<rest of docstring>
"""
```

## Promotion Rules

### CONCEPT → PARTIAL
- [ ] At least one function works
- [ ] Data structures defined
- [ ] Tests exist (even if failing)
- [ ] Clear path to REAL documented

### PARTIAL → REAL
- [ ] All simulation code replaced
- [ ] Backend endpoint wired (if applicable)
- [ ] `tests/real/` tests pass
- [ ] No TODO/FIXME in critical path
- [ ] STATUS header updated
- [ ] `STATUS.md` updated
- [ ] Second pair of eyes reviewed

### REAL → NEVER DOWNGRADE
- If a REAL component breaks, fix it. Don't relabel as PARTIAL.
- If architecture changes, write migration plan.

## Forbidden Words

Never use these in code comments, docstrings, or documentation:

- ❌ "world-ready"
- ❌ "100% secure"
- ❌ "production-grade" (unless audited)
- ❌ "fully implemented" (unless 68+ tests pass)
- ❌ "supercomputer" (unless running on HPC)
- ❌ "all sectors connected" (unless integration tests prove it)

**Use instead:**
- ✅ "prototype with real core"
- ✅ "beta with working backend"
- ✅ "security framework (audit pending)"
- ✅ "tested and passing"
- ✅ "vision architecture"

## PR Checklist

Before submitting PR:
- [ ] All touched files have STATUS header
- [ ] Tests added for new logic
- [ ] `pytest tests/real/ tests/prototype/ tests/integration/` passes
- [ ] `STATUS.md` updated if component status changed
- [ ] No forbidden words in new docs
- [ ] `TRUTH.md` not contradicted

## Enforcement

CI will reject PRs that:
1. Add .py files without STATUS header
2. Claim REAL without `tests/real/` tests
3. Use forbidden words in docstrings
4. Contradict `TRUTH.md`
