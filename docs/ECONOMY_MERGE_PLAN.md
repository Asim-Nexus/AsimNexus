# AsimNexus Economy Layer - Merge Plan

## Current Structure
```
economy/                   # ROOT (6 files)
├── escrow.py
├── marketplace.py
├── nexus_credits.py
├── staking.py
├── tokens.py
├── wallet.py
└── __init__.py

core/economy/              # CORE (10 files)
├── contract_executor.py
├── hybrid_economy.py
├── job_marketplace.py
├── marketplace_engine.py
├── nexus_credits.py
├── reputation_system.py
├── sovereign_token.py
├── task_bus.py
├── token_bridge.py
└── __init__.py
```

## Merged Structure
```
economy/
├── wallet.py               # User wallet management
├── tokens.py               # Token registry & minting
├── escrow.py               # Escrow transactions
├── marketplace.py          # Marketplace engine
├── staking.py              # Staking positions
├── credits.py              # Nexus Credits (consolidated)
├── contracts/              # Contracts (from core/economy)
│   └── __init__.py
├── reputation/             # Reputation system
│   └── __init__.py
└── __init__.py             # Unified exports
```

## Merge Actions
1. Consolidate `nexus_credits.py` duplicates
2. Move contracts from `core/economy/` to `economy/contracts/`
3. Move reputation to `economy/reputation/`
4. Update imports in `app.py`