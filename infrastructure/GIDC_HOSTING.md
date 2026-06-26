# AsimNexus GIDC Hosting Plan

## GIDC (Government Integrated Data Center) Registration

### Requirements
- Company Registration: AsimNexus Pvt. Ltd. or Gov Partnership
- Domain: api.asimnexus.gov.np (requires .gov.np registration)
- Security Clearance Certificate
- Technical Specification Document

### Application Process
```bash
# Step 1: Contact DoIT
Email: doit@mocit.gov.np
Phone: 01-4413117

# Step 2: Submit Documents
- Company Registration (कम्पनी दर्ता)
- Technical Proposal (प्राविधिक प्रस्ताव)
- Security Compliance Certificate
- Hosting Requirements (3-tier architecture)

# Step 3: Approval Timeline
- Initial Review: 3-5 days
- Technical Evaluation: 1 week
- Final Approval: 2-3 days
```

## Estimated Costs (NPR)

| Item | Cost | Notes |
|------|------|-------|
| GIDC Hosting (Annual) | 200,000 - 500,000 | Based on resources |
| .gov.np Domain | Free | Govt domains are free |
| SSL Certificate | Included | GIDC provides |
| Technical Setup | 50,000 - 100,000 | One-time setup |

## GIDC Deployment Configuration
```yaml
# k8s/gov-deployment.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: asimnexus-gov
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: asimnexus-backend
  namespace: asimnexus-gov
spec:
  replicas: 3
  selector:
    matchLabels:
      app: asimnexus
  template:
    metadata:
      labels:
        app: asimnexus
    spec:
      containers:
      - name: backend
        image: asimnexus/backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: NEPAL_ONLY
          value: "true"
        - name: DOMAIN
          value: "api.asimnexus.gov.np"
---
apiVersion: v1
kind: Service
metadata:
  name: asimnexus-service
  namespace: asimnexus-gov
spec:
  type: LoadBalancer
  ports:
  - port: 443
    targetPort: 8000
```

## Contact Points
- **DoIT**: डिजिटल विकास विभाग, मन्त्रालय सञ्चार तथा सूचना प्रविधि
- **Email**: doit@mocit.gov.np
- **Phone**: ०१-४४१३११७
- **Address**: मानवभवन, हातेबाटो, काठमाडौं