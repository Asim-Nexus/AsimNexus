# Release Freeze — v1.0.1

**Status**: ❄️ FROZEN (as of 2026-06-01)

## Branch Structure
- `main` — Active development for v1.2+
- `release/v1.0.1` — ❄️ Frozen release candidate (NO direct commits)
- `hotfix/*` — Emergency bugfix branch (from `release/v1.0.1`, PR back to `release/v1.0.1` AND `main`)

## What is frozen
- All new feature development targeting v1.0.1
- All protocol/API changes
- All dependency version bumps
- All refactoring beyond bugfix scope

## What is allowed
- Critical security patches (→ `hotfix/security-*`)
- Data-loss bugfixes (→ `hotfix/critical-*`)
- Documentation updates (→ direct to `release/v1.0.1` with review)

## How to hotfix
1. `git checkout release/v1.0.1`
2. `git checkout -b hotfix/description-of-fix`
3. Fix + test
4. PR into `release/v1.0.1` AND `main`
5. Tag: `git tag v1.0.1-hotfix.N`

## Release Cadence
- v1.0.1: Current freeze
- v1.2: Post-freeze (desktop/mobile platform, advanced UX)
