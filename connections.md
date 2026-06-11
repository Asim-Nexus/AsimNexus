# AsimNexus — Connection Registry

> **Version:** 1.0  
> **Framework:** Tier-1 Universal Data Domains  
> **Updated:** Per `/audit` cycle  

---

## Tier-1 Universal Data Domains

Every AsimNexus AIOS must connect to these 7 domains. Each connection is rated: **REAL** (working), **PARTIAL** (needs work), or **CONCEPT** (planned).

| # | Domain | Adapter / Module | Status | Auth Method | Notes |
|---|--------|-----------------|--------|-------------|-------|
| 1 | **Email** | [`connectors/google_ecosystem.py`](connectors/google_ecosystem.py) | ✅ REAL | OAuth 2.0 | Gmail read/send |
| 2 | **Calendar** | [`connectors/google_ecosystem.py`](connectors/google_ecosystem.py) | ✅ REAL | OAuth 2.0 | Events, scheduling |
| 3 | **Files / Documents** | `storage/`, `mesh/storage/` | ✅ REAL | Local FS + Mesh | Offline-first storage |
| 4 | **Chat / Messaging** | [`connectors/unified_messaging_connector.py`](connectors/unified_messaging_connector.py) | ✅ REAL | Multiple | Multi-platform unified |
| 5 | **Payment / Finance** | [`connectors/nepal_banking.py`](connectors/nepal_banking.py), [`core/finance/`](core/finance/) | ✅ REAL | API keys + OAuth | Nepal banking, wallets, crypto |
| 6 | **Government / Identity** | [`core/government/`](core/government/), [`core/identity/`](core/identity/) | ⚠️ PARTIAL | e-ID / DID | e-Residency, tax, signatures |
| 7 | **Mesh / Peers** | [`mesh/offline_sync_engine.py`](mesh/offline_sync_engine.py), [`runtime/zero_latency_mesh.py`](runtime/zero_latency_mesh.py) | ✅ REAL | P2P keys + DHT | Offline-capable federation |

---

## Expanded Connection Details

### 1. Email
- **Adapter:** [`connectors/google_ecosystem.py`](connectors/google_ecosystem.py)
- **Capabilities:** Read inbox, send emails, search threads, manage labels
- **Veto Gate:** Drafting/sending checked by Dharma Veto
- **Human Approval:** Required for sending on behalf of government/legal identities

### 2. Calendar
- **Adapter:** [`connectors/google_ecosystem.py`](connectors/google_ecosystem.py)
- **Capabilities:** List events, create/update events, check availability, meeting scheduling
- **Veto Gate:** Modification of existing events requires confirmation

### 3. Files & Documents
- **Storage:** `storage/` (local), `mesh/storage/` (distributed)
- **Capabilities:** CRUD operations, search, version tracking, offline sync
- **Veto Gate:** DELETE operations require human confirmation
- **Sovereign Data:** Never leaves device without explicit ZKP consent

### 4. Chat & Messaging
- **Adapter:** [`connectors/unified_messaging_connector.py`](connectors/unified_messaging_connector.py)
- **Capabilities:** Unified inbox, send/receive across platforms, auto-reply
- **Veto Gate:** Auto-reply and message sending checked for impersonation/deception

### 5. Payment & Finance
- **Adapters:** [`connectors/nepal_banking.py`](connectors/nepal_banking.py), [`core/finance/`](core/finance/)
- **Capabilities:** Wallet management, currency conversion, payments, escrow, crypto
- **Veto Gate:** Transactions above `ASIM_VETO_FINANCE_THRESHOLD` ($1,000 default) require human confirm
- **Audit:** Every financial action logged to immutable audit trail

### 6. Government & Identity
- **Modules:** [`core/government/`](core/government/), [`core/identity/`](core/identity/)
- **Capabilities:** Digital identity (DID), e-Residency, tax filing, e-signatures, government services
- **Veto Gate:** **Human Level-3 required** for all government/legal actions
- **Status:** ⚠️ PARTIAL — Identity creation/verification works; full government integration in progress

### 7. Mesh & Peers
- **Modules:** [`mesh/offline_sync_engine.py`](mesh/offline_sync_engine.py), [`runtime/zero_latency_mesh.py`](runtime/zero_latency_mesh.py)
- **Capabilities:** Peer discovery (DHT), offline operation, CRDT sync, air-gap mode, federation
- **Veto Gate:** Federation join requests require consent
- **Sovereignty:** Air-gap mode isolates from internet; mesh sync is opt-in

---

## Connection Health

Use `/api/integration/health` to check all connection statuses:

```bash
curl http://localhost:8000/api/integration/health
```

Use `/audit` skill to score connection health per domain (0-25 pts, /100 total).

---

## Adding a New Connection

1. Create adapter in `connectors/` following existing patterns
2. Register in this table
3. Wire to Dharma Veto check at integration points
4. Add integration test in `tests/real/`
5. Document in `connections.md` with status
