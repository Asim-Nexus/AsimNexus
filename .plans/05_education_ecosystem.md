# AsimNexus Nepal Ecosystem — Education Ecosystem

## Education Ecosystem — शिक्षा

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                    EDUCATION ECOSYSTEM                                                              │
│                    "नेपालको शैक्षिक डिजिटल संसार"                                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Structure

| Level | Entities | Count |
|-------|----------|-------|
| Universities | विश्वविद्यालय | १२+ |
| Schools | विद्यालय | २८,०००+ |
| Exams | परीक्षा | ३+ |

## 1. विश्वविद्यालय — १२+ Universities

| University | File | Location |
|------------|------|----------|
| त्रिभुवन विश्वविद्यालय | `universities/tribhuvan.py` | काठमाडौं |
| काठमाडौं विश्वविद्यालय | `universities/kathmandu.py` | काठमाडौं |
| पोखरा विश्वविद्यालय | `universities/pokhara.py` | पोखरा |
| पूर्वाञ्चल विश्वविद्यालय | `universities/purbanchal.py` | भारते |
| नेपाल संस्कृत विश्वविद्यालय | `universities/nepal_sanskrit.py` | काठमाडौं |
| कृषि विश्वविद्यालय | `universities/agriculture.py` | नेपालगञ्ज |
| नेपाल मेडिकल विश्वविद्यालय | `universities/medical.py` | काठमाडौं |
| नेपाल खुला विश्वविद्यालय | `universities/open.py` | भरिको |
| तराई विश्वविद्यालय | `universities/tarai.py` | सिरहा |
| सुदूरपश्चिम विश्वविद्यालय | `universities/far_western.py` | स्याङ्जा |

## 2. विद्यालय — २८,०००+ Schools

| Category | Files | Count |
|----------|-------|-------|
| Higher Secondary | `schools/higher_secondary/*.py` | १,५००+ |
| Secondary | `schools/secondary/*.py` | ७,०००+ |
| Primary | `schools/primary/*.py` | २८,०००+ |
| Total | | २८,०००+ |

## 3. परीक्षा — Exams

| Board | File | Purpose |
|-------|------|---------|
| नेपाल शिक्षा बोर्ड (NEB) | `exams/neb.py` | SLC/+2 |
| स्वायत्त तालीम संस्थान (CTEVT) | `exams/ctevt.py` | तालीम परीक्षा |
| विश्वविद्यालय परीक्षा | `exams/university.py` | विश्वविद्यालय |

## File Structure

```
backend/connectors/education/
├── __init__.py
├── universities/
│   ├── university_base.py
│   ├── tribhuvan.py
│   ├── kathmandu.py
│   ├── pokhara.py
│   └── ... (सबै १२+)
├── schools/
│   ├── school_base.py
│   ├── higher_secondary/
│   │   ├── hs_001.py
│   │   └── ... (१,५००+)
│   ├── secondary/
│   │   ├── sec_001.py
│   │   └── ... (७,०००+)
│   └── primary/
│       ├── pri_001.py
│       └── ... (२८,०००+)
└── exams/
    ├── neb.py
    ├── ctevt.py
    └── university_exams.py
```

## Stats

| Metric | Count |
|--------|-------|
| Files | ~28,012 |
| Lines | ~8,403,600 |
| Priority | 🟡 MEDIUM |