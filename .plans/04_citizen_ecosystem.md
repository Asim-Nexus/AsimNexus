# AsimNexus Nepal Ecosystem — Citizen Ecosystem

## Citizen Ecosystem (Local-First) — नागरिक

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                    CITIZEN ECOSYSTEM (Local-First)                                               │
│                    "प्रत्येक नागरिकको आफ्नै डिजिटल संसार"                                          │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Structure

| Layer | Components |
|-------|------------|
| Identity | Digital Twin (HDT) |
| Personal | Health, Education, Finance, Schedule |
| Family | Members, Shared Calendar, Finance |
| Work | Employment, Skills, Projects |

## Citizen Layers

### 1. Personal Layer

| Module | File | Purpose |
|--------|------|---------|
| Digital Twin | `personal_os.py` | HDT अभिन्न पहिचान |
| Health Records | `health.py` | स्वास्थ्य इतिहास |
| Education | `education.py` | शिक्षा इतिहास |
| Finance | `finance.py` | वित्त ट्र्याकिङ |
| Schedule | `schedule.py` | तालिका |
| Goals | `goals.py` | लक्ष्य |
| Habits | `habits.py` | बानी |
| Photos | `photos.py` | फोटो |
| Documents | `documents.py` | कागजात |
| Memories | `memories.py` | सम्झना |

### 2. Family Layer

| Module | File | Purpose |
|--------|------|---------|
| Family Members | `family.py` | परिवारजनसँग जोड्ने |
| Family Finance | `family/finance.py` | साझा वित्त |
| Legacy Notebook | `legacy.py` | वारसा नोटबुक |
| Shared Calendar | `family/calendar.py` | परिवार तालिका |

### 3. Work Layer

| Module | File | Purpose |
|--------|------|---------|
| Employment | `work.py` | रोजगार |
| Skills | `skills.py` | सीप विकास |
| Projects | `projects.py` | प्रोजेक्ट |
| Network | `work/network.py` | सम्पर्क नेटवर्क |
| Job Marketplace | `work/job_marketplace.py` | रोजगार बजार |

## File Structure

```
backend/citizen/
├── __init__.py
├── personal_os.py
├── digital_twin.py
├── health.py
├── education.py
├── finance.py
├── schedule.py
├── goals.py
├── habits.py
├── photos.py
├── documents.py
├── memories.py
├── family/
├── work/
├── legacy/
└── ecosystem/
```

## Stats

| Metric | Count |
|--------|-------|
| Files per Citizen | ~100+ |
| Lines | ~100,000+ |
| Data Sovereignty | 100% Local-First |