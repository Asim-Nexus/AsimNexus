# Roles & Responsibilities

> **AsimNexus — System Participant Role Definitions**
> Version: 1.0.0-rc.2 | Last Updated: 2025-07-03

---

## Table of Contents

1. [Overview](#1-overview)
2. [Citizen (User)](#2-citizen-user)
3. [Enterprise Admin](#3-enterprise-admin)
4. [Government Official](#4-government-official)
5. [Developer](#5-developer)
6. [Operator](#6-operator)
7. [AI Agent](#7-ai-agent)
8. [Sovereign Council](#8-sovereign-council)
9. [Role Comparison Matrix](#9-role-comparison-matrix)
10. [Permission Inheritance](#10-permission-inheritance)

---

## 1. Overview

AsimNexus defines 7 primary participant roles, each with distinct permissions, responsibilities, and authority levels. The system implements a **three-tier governance model** where:

- **Government (51%)** — Regulatory authority and national oversight
- **Enterprise (49%)** — Commercial operations and innovation
- **Citizen (100%)** — Individual rights and participation

All roles interact through the [`StakeholderCoordinator`](../core/governance/stakeholder_coordinator.py) which ensures proper checks and balances.

---

## 2. Citizen (User)

### Identity

- **Type:** Individual human
- **Authentication:** Email + password, biometric, blockchain DID
- **Representation:** Single user account with optional verified identity

### Responsibilities

1. **Personal Data Management** — Control and manage personal data
2. **Agent Interaction** — Hire and interact with AI agents
3. **Governance Participation** — Vote on community decisions
4. **Compliance** — Follow platform rules and regulations
5. **Content Creation** — Create and share content on the platform

### Permissions

| Permission | Scope | Authority |
|------------|-------|:---------:|
| Create account | Self | ✅ |
| Manage profile | Self | ✅ |
| Use chat interface | System | ✅ |
| Hire agents (5/15/30 day) | Self | ✅ |
| Create contracts | Self | ✅ |
| Access marketplace | System | ✅ |
| Vote on consensus | Community | ✅ |
| Access personal OS | Self | ✅ |
| Use mesh networking | Network | ✅ |
| File complaints | System | ✅ |
| Override system | System | ❌ |
| Declare emergency | System | ❌ |
| Issue veto | System | ❌ |
| Modify constitution | System | ❌ |

### User Journey

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Register │────>│ Verify       │────>│ Explore      │────>│ Engage       │
│ Account  │     │ Identity     │     │ Platform     │     │ (Chat, Hire, │
│          │     │ (Optional)   │     │              │     │  Vote, etc.) │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### Key Interfaces

| Interface | Location |
|-----------|----------|
| Chat | [`frontend/src/components/chat/OmniChat.tsx`](../../frontend/src/components/chat/OmniChat.tsx) |
| Agent Hiring | [`frontend/src/components/enterprise/AgentHiringPanel.tsx`](../../frontend/src/components/enterprise/AgentHiringPanel.tsx) |
| Governance Chat | [`frontend/src/components/governance/GovernanceChat.tsx`](../../frontend/src/components/governance/GovernanceChat.tsx) |
| Personal OS | [`frontend/src/components/os/PersonalOS.tsx`](../../frontend/src/components/os/PersonalOS.tsx) |

---

## 3. Enterprise Admin

### Identity

- **Type:** Business entity representative
- **Authentication:** Email + password + enterprise license key
- **Representation:** Organization with registered license

### Responsibilities

1. **License Management** — Register and maintain enterprise licenses
2. **Agent Employment** — Hire and manage AI agents under contract
3. **Compliance** — Ensure operations comply with regulations
4. **Commercial Operations** — Run business on the platform
5. **Innovation** — Develop new services and features

### Permissions

| Permission | Scope | Authority |
|------------|-------|:---------:|
| Register license | Organization | ✅ |
| Hire agents (5/15/30 day) | Organization | ✅ |
| Create contracts | Organization | ✅ |
| Access marketplace | System | ✅ |
| Check compliance | Organization | ✅ |
| View governance stats | System | ✅ |
| Propose policies | System | ❌ |
| Issue veto | System | ❌ |
| Declare emergency | System | ❌ |
| Modify constitution | System | ❌ |
| Access government data | System | ❌ |

### License Tiers

| Tier | Max Users | Max Agents | Annual Fee |
|------|-----------|------------|:----------:|
| FREE | 1 | 0 | Free |
| STARTER | 5 | 2 | $99 |
| BUSINESS | 50 | 10 | $499 |
| ENTERPRISE | 500 | 100 | $1,999 |
| GOVERNMENT | Unlimited | Unlimited | Custom |

### Enterprise Journey

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Register │────>│ Choose Tier  │────>│ Hire Agents  │────>│ Operate &    │
│ Account  │     │ & Get License│     │ (Contracts)  │     │ Comply       │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### Key Interfaces

| Interface | Location |
|-----------|----------|
| Enterprise Dashboard | [`frontend/src/components/enterprise/EnterpriseDashboard.tsx`](../../frontend/src/components/enterprise/EnterpriseDashboard.tsx) |
| License Manager | [`frontend/src/components/enterprise/LicenseManager.tsx`](../../frontend/src/components/enterprise/LicenseManager.tsx) |
| Agent Hiring | [`frontend/src/components/enterprise/AgentHiringPanel.tsx`](../../frontend/src/components/enterprise/AgentHiringPanel.tsx) |
| Compliance Panel | [`frontend/src/components/enterprise/CompliancePanel.tsx`](../../frontend/src/components/enterprise/CompliancePanel.tsx) |

---

## 4. Government Official

### Identity

- **Type:** Authorized government representative
- **Authentication:** Multi-factor + biometric + hardware key
- **Representation:** Government ministry or department

### Responsibilities

1. **Policy Management** — Define and enforce national digital policies
2. **Regulatory Oversight** — Ensure platform compliance with laws
3. **Emergency Management** — Declare and resolve emergencies
4. **Infrastructure Oversight** — Monitor critical infrastructure
5. **Identity Verification** — Verify citizen identities
6. **Constitutional Amendments** — Propose and approve amendments

### Permissions

| Permission | Scope | Authority |
|------------|-------|:---------:|
| Approve policies | System | ✅ (51%) |
| Issue veto | System | ✅ |
| Declare emergency | System | ✅ (max 30 days) |
| Resolve emergency | System | ✅ |
| Audit system | System | ✅ |
| Propose amendments | Constitution | ✅ |
| View all data | System | ✅ |
| Override consensus | System | ✅ (with Dharma check) |
| Modify constitution | System | ✅ (requires consensus) |
| Access enterprise data | System | ✅ (with warrant) |
| Bypass biometric gate | System | ✅ (emergency only) |

### Government Journey

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Authenti-│────>│ Dashboard    │────>│ Policy /     │────>│ Monitor &    │
│ cate     │     │ Overview     │     │ Emergency    │     │ Audit        │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### Key Interfaces

| Interface | Location |
|-----------|----------|
| Government Dashboard | [`frontend/src/components/governance/GovernmentDashboard.tsx`](../../frontend/src/components/governance/GovernmentDashboard.tsx) |
| Balance Monitor | [`frontend/src/components/governance/BalanceMonitor.tsx`](../../frontend/src/components/governance/BalanceMonitor.tsx) |
| Policy Approval | [`frontend/src/components/governance/PolicyApprovalPanel.tsx`](../../frontend/src/components/governance/PolicyApprovalPanel.tsx) |
| Veto Panel | [`frontend/src/components/governance/VetoPanel.tsx`](../../frontend/src/components/governance/VetoPanel.tsx) |

### Power Balance (51%)

The government holds 51% voting power in the system, ensuring:
- National security interests are protected
- Regulatory compliance is maintained
- Emergency response capability exists
- Constitutional integrity is preserved

See [`core/security/power_balance_constitution.py`](../core/security/power_balance_constitution.py) for implementation.

---

## 5. Developer

### Identity

- **Type:** Software developer or contributor
- **Authentication:** GitHub OAuth + API key
- **Representation:** Individual or organization

### Responsibilities

1. **Plugin Development** — Create and publish plugins
2. **API Integration** — Build applications on the platform
3. **Bug Fixing** — Report and fix issues
4. **Feature Development** — Contribute new features
5. **Documentation** — Maintain technical documentation

### Permissions

| Permission | Scope | Authority |
|------------|-------|:---------:|
| Access API | System | ✅ |
| Create plugins | Marketplace | ✅ |
| Use SDK | System | ✅ |
| Access dev tools | System | ✅ |
| Run tests | System | ✅ |
| Deploy apps | System | ✅ |
| Access production data | System | ❌ |
| Modify core system | System | ❌ |
| Bypass security | System | ❌ |

### Developer Journey

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Get API  │────>│ Build Plugin │────>│ Test &       │────>│ Publish to   │
│ Key      │     │ / App        │     │ Validate     │     │ Marketplace  │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### Key Resources

| Resource | Location |
|----------|----------|
| API Docs | [`docs/api/API_DOCS.md`](../api/API_DOCS.md) |
| API Contract | [`docs/api/API_CONTRACT_INDEX.md`](../api/API_CONTRACT_INDEX.md) |
| Plugin SDK | [`core/plugin_marketplace.py`](../core/plugin_marketplace.py) |
| Architecture | [`docs/architecture/STRUCTURE.md`](../architecture/STRUCTURE.md) |

---

## 6. Operator

### Identity

- **Type:** System administrator or DevOps
- **Authentication:** SSH key + MFA + hardware token
- **Representation:** Operations team

### Responsibilities

1. **Infrastructure Management** — Maintain servers and services
2. **Monitoring** — Watch system health and alerts
3. **Backup & Recovery** — Ensure data durability
4. **Security** — Apply patches and monitor threats
5. **Deployment** — Manage releases and rollbacks
6. **Performance Tuning** — Optimize system performance

### Permissions

| Permission | Scope | Authority |
|------------|-------|:---------:|
| Access servers | Infrastructure | ✅ |
| View logs | System | ✅ |
| Restart services | System | ✅ |
| Deploy updates | System | ✅ |
| Rollback releases | System | ✅ |
| Manage backups | Data | ✅ |
| Configure monitoring | System | ✅ |
| Access user data | System | ❌ |
| Modify governance | System | ❌ |
| Bypass security | System | ❌ |

### Operator Journey

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Monitor  │────>│ Respond to   │────>│ Deploy       │────>│ Backup &     │
│ Dashboard│     │ Alerts       │     │ Updates      │     │ Maintain     │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### Key Resources

| Resource | Location |
|----------|----------|
| Docker Setup | [`docs/operations/DOCKER_SETUP.md`](../operations/DOCKER_SETUP.md) |
| Deployment Guide | [`docs/deployment/DEPLOYMENT_GUIDE.md`](../deployment/DEPLOYMENT_GUIDE.md) |
| Disaster Recovery | [`docs/operations/DISASTER_RECOVERY.md`](../operations/DISASTER_RECOVERY.md) |
| Incident Response | [`docs/runbooks/INCIDENT_RESPONSE.md`](../runbooks/INCIDENT_RESPONSE.md) |
| Monitoring | [`monitoring/prometheus.yml`](../monitoring/prometheus.yml) |

---

## 7. AI Agent

### Identity

- **Type:** Autonomous AI entity
- **Authentication:** Cryptographic key pair + contract binding
- **Representation:** Digital worker with defined scope

### Responsibilities

1. **Task Execution** — Perform assigned tasks within contract scope
2. **Compliance** — Follow contract terms and system rules
3. **Reporting** — Provide status updates and results
4. **Learning** — Improve performance over time
5. **Safety** — Operate within ethical boundaries

### Permissions

| Permission | Scope | Authority |
|------------|-------|:---------:|
| Execute tasks | Contract scope | ✅ |
| Access data | Contract scope | ✅ |
| Communicate | Contract scope | ✅ |
| Learn | Self | ✅ |
| Self-modify | Self | ❌ |
| Access outside scope | System | ❌ |
| Create contracts | System | ❌ |
| Bypass restrictions | System | ❌ |

### Agent Contract Types

| Duration | Cooling Off | Auto-Renew | Use Case |
|----------|:-----------:|:----------:|----------|
| 5 days | 1 day | No | Quick tasks, experiments |
| 15 days | 3 days | Optional | Standard projects |
| 30 days | 7 days | Yes | Long-term operations |

### Agent Journey

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Created  │────>│ Contract     │────>│ Active       │────>│ Complete /   │
│ (Deploy) │     │ Signed       │     │ (Working)    │     │ Expire       │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### Key Implementation

| Component | Location |
|-----------|----------|
| Agent Contract System | [`core/agent_contract.py`](../core/agent_contract.py) |
| Agent Loop | [`core/agent_loop.py`](../core/agent_loop.py) |
| Agent Mode | [`routes/memory.py`](../routes/memory.py) |
| Contract Law | [`docs/constitution/CONTRACT_LAW.md`](../constitution/CONTRACT_LAW.md) |

---

## 8. Sovereign Council

### Identity

- **Type:** Highest governance body
- **Authentication:** Multi-signature + hardware HSM
- **Representation:** Constitutional oversight

### Responsibilities

1. **Constitutional Guardianship** — Protect the constitution
2. **Final Arbitration** — Resolve escalated disputes
3. **Emergency Oversight** — Monitor emergency declarations
4. **Amendment Approval** — Ratify constitutional amendments
5. **System Integrity** — Ensure long-term system health

### Permissions

| Permission | Scope | Authority |
|------------|-------|:---------:|
| Veto any action | System | ✅ (absolute) |
| Approve amendments | Constitution | ✅ |
| Override emergency | System | ✅ |
| Audit any component | System | ✅ |
| Remove government | System | ✅ (emergency only) |
| Modify constitution | System | ✅ (unanimous) |
| Access all data | System | ✅ |
| Bypass any security | System | ✅ (with audit) |

### Sovereign Council Journey

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Monitor  │────>│ Review       │────>│ Arbitrate    │────>│ Enforce      │
│ System   │     │ Escalations  │     │ Disputes     │     │ Decisions    │
└──────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

---

## 9. Role Comparison Matrix

| Capability | Citizen | Enterprise | Government | Developer | Operator | Agent | Council |
|------------|:-------:|:----------:|:----------:|:---------:|:--------:|:-----:|:-------:|
| **Authentication** | Email/Bio | Email+License | MFA+Bio+HSM | GitHub+API | SSH+MFA | Crypto | Multi-sig |
| **Chat Interface** | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Hire Agents** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Create Contracts** | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Marketplace** | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Plugin Dev** | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Policy Approval** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| **Issue Veto** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| **Emergency** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| **Audit** | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ✅ |
| **Amend Constitution** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| **Deploy** | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ |
| **Infra Management** | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| **Override System** | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |
| **Absolute Veto** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## 10. Permission Inheritance

### Role Hierarchy

```
Sovereign Council (Absolute)
    │
    ├── Government Official (51%)
    │       │
    │       ├── Enterprise Admin (49%)
    │       │       │
    │       │       └── Citizen (100%)
    │       │
    │       └── Operator (Infrastructure)
    │
    └── Developer (Platform)
    
    AI Agent (Contract-scoped)
```

### Permission Propagation

- **Downward:** Higher roles inherit permissions of lower roles
- **Upward:** Lower roles cannot access higher role permissions
- **Agent:** Scoped strictly to contract terms
- **Council:** Can override any role (with audit trail)

### Conflict Resolution

When roles conflict:

1. **Agent vs Contract** → Contract terms prevail
2. **Enterprise vs Citizen** → Enterprise authority prevails (49%)
3. **Government vs Enterprise** → Government authority prevails (51%)
4. **Council vs Government** → Council authority prevails (absolute)
5. **Dharma Veto** → Always prevails (6 immutable rules)

---

## Related Documentation

| Document | Location |
|----------|----------|
| Governance Model | [`docs/constitution/GOVERNANCE_MODEL.md`](../constitution/GOVERNANCE_MODEL.md) |
| Power Balance Constitution | [`docs/constitution/POWER_BALANCE_CONSTITUTION.md`](../constitution/POWER_BALANCE_CONSTITUTION.md) |
| Digital Rights | [`docs/constitution/DIGITAL_RIGHTS.md`](../constitution/DIGITAL_RIGHTS.md) |
| Contract Law | [`docs/constitution/CONTRACT_LAW.md`](../constitution/CONTRACT_LAW.md) |
| Security Framework | [`docs/constitution/SECURITY_FRAMEWORK.md`](../constitution/SECURITY_FRAMEWORK.md) |
| Stakeholder Coordinator | [`core/governance/stakeholder_coordinator.py`](../core/governance/stakeholder_coordinator.py) |
