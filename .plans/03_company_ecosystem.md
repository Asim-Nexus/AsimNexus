# AsimNexus Nepal Ecosystem — Company Ecosystem

## Company Ecosystem (49%) — निजी क्षेत्र

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                    COMPANY ECOSYSTEM (49%)                                                       │
│                    "नेपालको व्यवसायिक डिजिटल संसार"                                                │
└─────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

## Structure

| Sector | Entities | Count |
|--------|----------|-------|
| वित्त | Banks | २७+ |
| टेलिकम | ISPs | ५८ |
| उद्योग | Companies | १००+ |
| ऊर्जा | Hydropower | १००+ |
| सेवा | Hotels/Tourism | ५००+ |

## 1. वित्त (Banks) — २७+ बैंक

### बैंक Connectors

| Bank | File | Type |
|------|------|------|
| नेपाल बैंक लिमिटेड (NBL) | `banks/nbl.py` | सरकारी |
| राष्ट्रिय बाणिज्य बैंक (RBB) | `banks/rbb.py` | सरकारी |
| नेपाल विकास बैंक (NABIL) | `banks/nabil.py` | निजी |
| विश्वा बैंक | `banks/vishwa.py` | निजी |
| ज्बोल्लेस्पार्स बैंक | `banks/standard_chartered.py` | विदेशी |
| नेपाल एसबीआई बैंक | `banks/nepal_sbi.py` | साझेदारी |
| क्यापिटल मेगा बैंक | `banks/mega.py` | निजी |
| सानिमा बैंक | `banks/sanima.py` | निजी |
| मक्सुरा बैंक | `banks/machhapuchchhre.py` | निजी |
| कुमारी बैंक | `banks/kumari.py` | निजी |
| प्राइम बैंक | `banks/prime.py` | निजी |
| सनराइज बैंक | `banks/sunrise.py` | निजी |
| नेपाल इन्भेस्टमेन्ट बैंक | `banks/nepal_investment.py` | निजी |
| अग्रिमा बैंक | `banks/agrima.py` | निजी |
| महेन्द्रा बैंक | `banks/mahendra.py` | निजी |
| प्रतिभा बैंक | `banks/prithvi.py` | निजी |
| सागरमाथा बैंक | `banks/sagarmata.py` | निजी |
| लक्ष्मी बैंक | `banks/laxmi.py` | निजी |
| शिवालया बैंक | `banks/shivalaxmi.py` | निजी |
| विजया बैंक | `banks/vijaya.py` | निजी |

## 2. टेलिकम (ISPs) — ५८ ISP

### ISP Connectors (Top 10)

| ISP | File | Coverage |
|-----|------|----------|
| वर्ल्डलिंक | `isp/worldlink.py` | काठमाडौं भएसँगै nationwide |
| डिश होम | `isp/dishhome.py` | नेपाल भरिको |
| नेपाल टेलिकम | `isp/ntc.py` | nationwide |
| भिआनेट | `isp/vianet.py` | काठमाडौं |
| क्लास्टिक टेक | `isp/classic_tech.py` | विराटनगर |
| सुबिसु | `isp/subisu.py` | भक्तपुर |
| वेबसर्फर | `isp/websurfer.py` | पोखरा |
| नेपाल केबल | `isp/nepal_cable.py` | नेपालगञ्ज |
| फाइबरनेट | `isp/fibernet.py` | धनगढी |
| स्कायलिंक | `isp/skylink.py` | विभिन्न |

## 3. ठूला समूह (Conglomerates)

| Conglomerate | File | Sector |
|--------------|------|--------|
| चौधरी ग्रुप | `conglomerates/cg.py` | उद्योग/सेवा |
| गोल्छा समूह | `conglomerates/golchha.py` | उद्योग |
| विष्णु समूह | `conglomerates/vishal.py` | व्यापार |
| कंडे समूह | `conglomerates/kande.py` | व्यापार |
| हिमालयन समूह | `conglomerates/himalayan.py` | टुरिज्म |
| सूर्य नेपाल | `conglomerates/surya_nepal.py` | उद्योग |
| बटलर्स नेपाल | `conglomerates/bottlers_nepal.py` | उद्योग |
| डाबुर नेपाल | `conglomerates/dabur_nepal.py` | उद्योग |

## 4. ऊर्जा (Hydropower) — १००+ प्रोजेक्ट

| Project | File | Capacity |
|---------|------|----------|
| अपर्णा (Upper Tamakoshi) | `hydropower/upper_tamakoshi.py` | 456 MW |
| चिलिमे | `hydropower/chilime.py` | 22 MW |
| मध्य मर्स्याङ्दी | `hydropower/middle_marsyangdi.py` | 70 MW |
| त्रिशुली | `hydropower/trishuli.py` | 24 MW |
| कूलेखानी | `hydropower/kulekhani.py` | 60 MW |
| उपेर भोटे कोसी | `hydropower/upper_bhote_koshi.py` | 45 MW |
| खिम्टी | `hydropower/khimti.py` | 60 MW |
| मोडी | `hydropower/modi.py` | 14 MW |
| झिम्रुक | `hydropower/jhimruk.py` | 12 MW |

## File Structure

```
backend/connectors/company/
├── banks/
│   ├── __init__.py
│   ├── bank_base.py
│   ├── nbl.py
│   ├── rbb.py
│   ├── nabil.py
│   └── ... (सबै २७+ बैंक)
├── isp/
│   ├── __init__.py
│   ├── isp_base.py
│   ├── worldlink.py
│   ├── dishhome.py
│   ├── ntc.py
│   ├── vianet.py
│   └── ... (सबै ५८ ISP)
├── conglomerates/
│   ├── cg.py
│   ├── golchha.py
│   └── ...
├── hydropower/
│   ├── hydropower_base.py
│   ├── upper_tamakoshi.py
│   └── ... (सबै १००+)
├── hotels/
│   └── ... (सबै ५००+)
└── transport/
    ├── pathao.py
    ├── indrive.py
    └── foodmandu.py
```

## Stats

| Metric | Count |
|--------|-------|
| Files | ~200+ |
| Lines | ~55,500+ |
| Priority | 🟡 MEDIUM |