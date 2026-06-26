# AsimNexus VAPT Security Audit Plan

## Nepal Government-Authorized Security Auditors

| Company | Location | Services | Est. Cost (NPR) | Timeline |
|---------|----------|----------|-----------------|----------|
| **Nepal CERT** | Kathmandu | Gov VAPT, Security Audit | Free (govt) | 2 weeks |
| **TechMinds** | Kathmandu | Full VAPT, PenTest | 150,000 - 300,000 | 1-2 weeks |
| **CloudSecure Nepal** | Lalitpur | VAPT + Compliance | 100,000 - 200,000 | 2 weeks |
| **Cybersecurity Nepal** | Biratnagar | Security Testing | 120,000 - 250,000 | 1-2 weeks |

## VAPT Process Steps

```python
# compliance/vapt_checklist.py
VAPT_CHECKLIST = {
    "phase_1": {
        "name": "Reconnaissance",
        "tasks": ["Port Scanning", "Service Detection", "Domain Info Gathering"],
        "tools": ["nmap", "nikto", "whatweb"],
        "duration": "2 days"
    },
    "phase_2": {
        "name": "Vulnerability Scan",
        "tasks": ["OWASP ZAP", "Nessus Scan", "API Security Test"],
        "tools": ["OWASP ZAP", "Burp Suite", "Nuclei"],
        "duration": "3 days"
    },
    "phase_3": {
        "name": "Penetration Testing",
        "tasks": ["Authentication Bypass", "SQL Injection", "XSS Attack"],
        "tools": ["Metasploit", "SQLMap", "Burp Suite"],
        "duration": "4 days"
    },
    "phase_4": {
        "name": "Reporting & Remediation",
        "tasks": ["Vulnerability Report", "Risk Rating", "Fix Recommendations"],
        "duration": "3 days"
    }
}
```

## Contact for Approval
- **Contact**: Nepal CERT (www.nepalcert.gov.np)
- **Email**: cert@mha.gov.np
- **Timeline**: 1 week application processing