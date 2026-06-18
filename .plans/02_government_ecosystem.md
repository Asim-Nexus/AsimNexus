# AsimNexus Nepal Ecosystem — Government Ecosystem

## Government Ecosystem (51%) — संघीय सरकार

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                    GOVERNMENT ECOSYSTEM (51%)                                                      │
│                    "नेपालको सार्वभौमिक डिजिटल राज्य"                                               │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Structure

| Level | Entities | Count |
|-------|----------|-------|
| Federal | Ministries + Constitutional Bodies | १८ + ९ = २७ |
| Provincial | Provinces | ७ |
| Local | Districts + Palikas + Wards | ७७ + ७५३ + ६,७४३ |

## 1. Federal Level — १८ मन्त्रालय + ९ संवैधानिक निकाय

### १८ मन्त्रालय (Ministries)

| Ministry | File | Purpose |
|----------|------|---------|
| प्रधानमन्त्री कार्यालय (PM Office) | `ministries/pm_office.py` | राष्ट्रपति/प्रधानमन्त्री |
| अर्थ मन्त्रालय (Finance) | `ministries/finance.py` | बजेट, कर, अर्थतन्त्र |
| गृह मन्त्रालय (Home) | `ministries/home.py` | प्रशासन, स्थानान्तरण |
| स्वास्थ्य मन्त्रालय (Health) | `ministries/health.py` | स्वास्थ्य सेवा, अस्पताल |
| शिक्षा मन्त्रालय (Education) | `ministries/education.py` | शिक्षा नीति, विद्यालय |
| कृषि मन्त्रालय (Agriculture) | `ministries/agriculture.py` | कृषि, खेती, उर्वरक |
| पर्यटन मन्त्रालय (Tourism) | `ministries/tourism.py` | पर्यटन, होटल, गाईड |
| ऊर्जा मन्त्रालय (Energy) | `ministries/energy.py` | ऊर्जा, हाइड्रोपावर |
| उद्योग मन्त्रालय (Industry) | `ministries/industry.py` | उद्योग, उद्यमपूरक |
| सूचना मन्त्रालय (Telecom) | `ministries/telecom.py` | सूचना, टेलिकम |
| भूमि मन्त्रालय (Land) | `ministries/land.py` | भूमि, अधिकार, कर |
| कानून मन्त्रालय (Law) | `ministries/law.py` | कानून, अदालत, वकील |
| परराष्ट्र मन्त्रालय (Foreign) | `ministries/foreign.py` | विदेश, राष्ट्र मध्यस्थन |
| रक्षा मन्त्रालय (Defense) | `ministries/defense.py` | सेना, सुरक्षा |
| विज्ञान मन्त्रालय (Science) | `ministries/science.py` | विज्ञान, प्रविधि |
| पूर्वाधार मन्त्रालय (Infrastructure) | `ministries/infrastructure.py` | सडक, पुर्वाधार |
| युवा मन्त्रालय (Youth) | `ministries/youth.py` | युवा, उद्यम, रोजगारी |
| महिला मन्त्रालय (Women) | `ministries/women.py` | महिला, समानता |

### ९ संवैधानिक निकायहरू

| Body | File | Purpose |
|------|------|---------|
| सर्वोच्च अदालत (Supreme Court) | `constitutional_bodies/supreme_court.py` | सर्वोच्च न्याय |
| उच्च अदालत (High Courts) | `constitutional_bodies/high_courts.py` | ७ वटा हाइ अदालत |
| नागरिक अभियान (CIAA) | `constitutional_bodies/ciaa.py` | भ्रष्टाचार निरोधी |
| ऐन संयन्त्र (Agni Sanyantra) | `constitutional_bodies/agni_sanyantra.py` | गुप्तचर |
| निर्वाचन आयोग (Election Commission) | `constitutional_bodies/election_commission.py` | निर्वाचन |
| लोकतान्त्रिक समिति | `constitutional_bodies/loktantra_samiti.py` | लोकतन्त्र सुधार |
| मानव अधिकार समिति | `constitutional_bodies/manuskritik_samiti.py` | मानव अधिकार |
| सामाजिक न्याय आयोग | `constitutional_bodies/samajik_nyay_aayog.py` | सामाजिक न्याय |
| राजसंविधा आयोग | `constitutional_bodies/rajya_samvidhan_aayog.py` | संविधान संशोधन |

## 2. Provincial Level — ७ प्रदेश

| Province | File | Headquarters |
|----------|------|--------------|
| प्रदेश १ (कोशी) | `provincial/province_1.py` | विजयपुर |
| प्रदेश २ (मधेश) | `provincial/province_2.py` | जनकपुर |
| प्रदेश ३ (बागमती) | `provincial/province_3.py` | हेमजुवा |
| प्रदेश ४ (गण्डकी) | `provincial/province_4.py` | पोखरा |
| प्रदेश ५ (लुम्बिनी) | `provincial/province_5.py` | वीरगञ्ज |
| प्रदेश ६ (कर्णाली) | `provincial/province_6.py` | बिरामा |
| प्रदेश ७ (सुदूरपश्चिम) | `provincial/province_7.py` | भद्रपुर |

## 3. Local Level — ७७ जिल्ला + ७५३ पालिका

### ७७ जिल्ला

| District | File | Type |
|----------|------|------|
| काठमाडौं | `districts/kathmandu.py` | Metropolitan |
| ललितपुर | `districts/lalitpur.py` | Metropolitan |
| भक्तपुर | `districts/bhaktapur.py` | Metropolitan |
| पोखरा | `districts/pokhara.py` | Sub-Metropolitan |
| विराटनगर | `districts/biratnagar.py` | Sub-Metropolitan |
| बुटवल | `districts/butwal.py` | Sub-Metropolitan |
| नेपालगञ्ज | `districts/nepalgunj.py` | Sub-Metropolitan |
| धनगढी | `districts/dhangadhi.py` | Sub-Metropolitan |
| विरगञ्ज | `districts/birgunj.py` | Sub-Metropolitan |
| जनकपुर | `districts/janakpur.py` | Sub-Metropolitan |
| ... | `districts/*.py` | सबै ७७ जिल्ला |

### ७५३ पालिका

| Type | Count | Path |
|------|-------|------|
| नगरपालिका | २९३ | `local_bodies/municipalities/*.py` |
| गाउँपालिका | ४६० | `local_bodies/rural_municipalities/*.py` |

## File Structure

```
backend/connectors/gov/
├── federal/
│   ├── ministries/
│   │   ├── __init__.py
│   │   ├── pm_office.py
│   │   ├── finance.py
│   │   ├── home.py
│   │   ├── health.py
│   │   ├── education.py
│   │   ├── agriculture.py
│   │   ├── tourism.py
│   │   ├── energy.py
│   │   ├── industry.py
│   │   ├── telecom.py
│   │   ├── land.py
│   │   ├── law.py
│   │   ├── foreign.py
│   │   ├── defense.py
│   │   ├── science.py
│   │   ├── infrastructure.py
│   │   ├── youth.py
│   │   └── women.py
│   └── constitutional_bodies.py
├── provincial/
│   ├── province_1.py
│   ├── province_2.py
│   ├── province_3.py
│   ├── province_4.py
│   ├── province_5.py
│   ├── province_6.py
│   └── province_7.py
└── local/
    ├── base_palika.py
    ├── municipalities/
    └── rural_municipalities/
```

## Stats

| Metric | Count |
|--------|-------|
| Files | ~855 |
| Lines | ~256,500 |
| Priority | 🚨 HIGH |