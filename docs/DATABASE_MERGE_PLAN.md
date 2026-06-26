# AsimNexus - Database Layer Merge Plan

## Current Structure
```
database/migrations/
├── company_schema.sql
├── gov_schema.sql
├── postgresql.py
├── user_schema.sql
└── __pycache__/

DigitalNepal-backend/database/
└── __init__.py
```

## Proposed Unified Structure
```
database/
├── schemas/
│   ├── government.sql      (Gov tables)
│   ├── companies.sql       (Bank, ISP tables)
│   ├── users.sql           (User profiles)
│   └── life_journey.sql    (Life Journey stages)
├── migrations/
│   └── postgresql.py       (Migration runner)
├── connectors/
│   └── supabase.py         (Supabase integration)
└── __init__.py             (Unified exports)
```

## Merge Steps
1. Consolidate SQL schemas to `database/schemas/`
2. Update `database/migrations/postgresql.py` with all models
3. Add Supabase connector
4. Create unified `__init__.py`