# AsimNexus Connectors - Unified Structure

## Current Structure
### Root connectors/ (75 files)
- LLM/API connectors: anthropic, gemini, openai, deepseek
- Sector connectors: education_api, health_api, tourism
- Integration connectors: oauth, cloudinary, supabase

### DigitalNepal-backend/connectors/ (5 main)
- `nepal_connectors.py` - 18 ministries, 7 provinces, 77 districts, 30 banks, 20 ISPs, 12 universities, 7 schools
- `health_connectors.py` - 12 hospitals
- `palika_connectors.py` - 753 palikas
- `tourism_connectors.py` - 20 hotels

## Unified Structure (After Merge)
```
connectors/
├── nepal/
│   ├── government.py      # Ministries, Provinces, Districts
│   ├── companies.py       # Banks, ISPs
│   ├── education.py       # Universities, Schools
│   └── __init__.py
├── health/
│   └── hospitals.py       # 12 hospitals
├── local/
│   └── palikas.py         # 753 palikas
├── tourism/
│   └── hotels.py          # 20 hotels
├── llms/
│   ├── openai.py
│   ├── anthropic.py
│   ├── gemini.py
│   └── __init__.py
├── sector/
│   ├── education_api.py
│   ├── health_api.py
│   └── __init__.py
└── __init__.py            # Unified export
```

## Merge Action Required
1. Move `DigitalNepal-backend/connectors/*` to `connectors/nepal/`
2. Consolidate `__init__.py` exports
3. Update `app.py` imports to use unified path