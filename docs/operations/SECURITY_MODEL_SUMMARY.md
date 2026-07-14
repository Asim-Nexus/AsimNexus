# Security Model Summary

> **AsimNexus v1.0.1** | Last updated: 2026-07-03
> Source: [`core/security/`](../../core/security/), [`core/orchestrator/tools/sandbox/docker_sandbox.py`](../../core/orchestrator/tools/sandbox/docker_sandbox.py)

---

## 1. Security Posture Overview

AsimNexus implements a **defense-in-depth** security architecture organized into three conceptual layers:

| Layer | Responsibility |
|-------|---------------|
| 🛡️ **PREVENT** | Authentication, agent registration, lockout policies |
| 🔒 **CONTAIN** | Sandboxing, permission scoping, capability enforcement |
| 🔍 **DETECT & RECOVER** | Audit logging, anomaly detection, kill switch, checkpoint rollback |

These layers are coordinated through the security middleware and access control systems in [`core/security/`](../../core/security/).

### Security Levels

Three sensitivity levels govern access control:

| Level | Usage | Example |
|-------|-------|---------|
| `standard` | General API access | Chat, memory retrieval |
| `sensitive` | User data operations | Biometric data, PII |
| `top_secret` | System-critical actions | Override approvals, hard-lock release |

---

## 2. Authentication

### 2.1 Methods

Supported authentication methods, defined in [`core/security/auth_middleware.py`](../../core/security/auth_middleware.py):

| Method | Status | Purpose |
|--------|--------|---------|
| `NONE` | Public | Health probes, static assets |
| `API_KEY` | Real | Machine-to-machine, service accounts |
| `OAUTH2` | Real | Third-party identity federation |
| `OIDC` | Real | OpenID Connect identity tokens |
| `MTLS` | Real | Mutual TLS for peer mesh nodes |
| `TICKET` | Real | Kerberos-style session tickets |

### 2.2 JWT Authentication

Defined in [`core/security/jwt.py`](../../core/security/jwt.py). The JWT system implements:

- **Token format**: JWT with HS256 signing
- **Session store**: SQLite-backed active sessions table
- **Lockout policy**: Tracks failed logins per IP + username combination
- **Token rotation**: Refresh tokens invalidate old access tokens on use
- **IP pinning**: Token verification includes client IP matching

**Endpoints:**

| Endpoint | Method | Source |
|----------|--------|--------|
| `/api/auth/register` | POST | [`routes/auth.py`](../../routes/auth.py) |
| `/api/auth/login` | POST | [`routes/auth.py`](../../routes/auth.py) |
| `/api/auth/verify` | POST | [`routes/auth.py`](../../routes/auth.py) |
| `/api/auth/logout` | POST | [`routes/auth.py`](../../routes/auth.py) |
| `/api/auth/sessions` | GET | [`routes/auth.py`](../../routes/auth.py) |
| `/api/auth/refresh` | POST | [`routes/auth.py`](../../routes/auth.py) |

### 2.3 Biometric Hardware Gate

Defined in [`core/security/biometric_hardware_gate.py`](../../core/security/biometric_hardware_gate.py). The [`BiometricHardwareGate`](../../core/security/biometric_hardware_gate.py:53) provides **Level-3** biometric verification with 7 states:

```mermaid
stateDiagram-v2
    [*] --> ARMED
    ARMED --> GRANTED: Biometric match
    ARMED --> DENIED: Biometric mismatch
    ARMED --> TIMEOUT: No response within window
    ARMED --> ESCALATED: Admin escalation
    TIMEOUT --> ARMED: Retry
    DENIED --> AUTO_LOCK: Max failures
    ESCALATED --> GRANTED: Admin approves
    AUTO_LOCK --> ARMED: Emergency bypass code
    BYPASSED --> ARMED: Reset
```

Key methods:

| Method | Purpose |
|--------|---------|
| [`arm_from_threat()`](../../core/security/biometric_hardware_gate.py:97) | Arm gate in response to detected threat |
| [`verify_and_lock()`](../../core/security/biometric_hardware_gate.py:174) | Verify biometric + execute system lock |
| [`verify_admin()`](../../core/security/biometric_hardware_gate.py:346) | Synchronous admin biometric check |
| [`emergency_bypass()`](../../core/security/biometric_hardware_gate.py:456) | Bypass with override code |
| [`authenticate()`](../../core/security/biometric_hardware_gate.py:530) | Full MFA authentication flow |

---

## 3. Authorization

### 3.1 Capability-Based Access Control

The security middleware in [`core/security/auth_middleware.py`](../../core/security/auth_middleware.py) implements a fine-grained permission model:

```python
@dataclass
class PermissionScope:
    resource: str          # e.g., "mesh", "storage", "consensus"
    action: str            # e.g., "read", "write", "admin"
    context: Dict          # Additional constraints
```

### 3.2 Access Decision Flow

The [`AuthMiddleware`](../../core/security/auth_middleware.py) orchestrates the full decision pipeline:

```mermaid
sequenceDiagram
    participant R as Request
    participant AM as AuthMiddleware
    participant JWT as JWT Verification
    participant RBAC as RBAC Check
    participant AUDIT as AuditLog

    R->>AM: Request with Bearer token
    AM->>JWT: decode_token(token)
    JWT-->>AM: user_id, role, scopes
    AM->>RBAC: check_permission(role, resource, action)
    RBAC-->>AM: allowed/denied
    AM->>AUDIT: log_action(entry)
    AUDIT-->>AM: logged
    AM-->>R: response (200/401/403)
```

### 3.3 Domain Veto Registry

Defined in [`core/consensus/consensus_engine.py`](../../core/consensus/consensus_engine.py). The veto system enforces domain-specific access boundaries:

| Domain | Veto Holder | Scope |
|--------|-------------|-------|
| `security` | clone_01 | All security policy changes |
| `sovereignty` | clone_02 | Constitutional/air-gap decisions |
| `finance` | Finance arbiter | Transaction approvals |
| `governance` | Governance arbiter | Policy modifications |
| `network` | Network arbiter | Mesh topology changes |
| `storage` | Storage arbiter | Data retention policies |
| `identity` | Identity arbiter | DID/key management |
| `learning` | Learning arbiter | Model promotion decisions |

---

## 4. Post-Quantum Cryptography

Defined in [`core/security/post_quantum_crypto.py`](../../core/security/post_quantum_crypto.py). PQC stubs provide NIST-standard algorithm signatures:

### 4.1 Algorithm Stubs

| Algorithm | Type | Public Key | Secret Key | Ciphertext/Sig |
|-----------|------|------------|------------|----------------|
| **Kyber-512** | KEM | 800 bytes | 1,632 bytes | 768 bytes |
| **Dilithium2** | Signature | 1,312 bytes | 2,528 bytes | 2,420 bytes |
| **FALCON-512** | Signature | 897 bytes | 1,281 bytes | 666 bytes |

Current provider is `software_fallback` (`PQC_PROVIDER` constant).

### 4.2 Key Operations

Defined through [`core/security/post_quantum_crypto.py`](../../core/security/post_quantum_crypto.py):

| Method | Purpose |
|--------|---------|
| `generate_quantum_keypair()` | Generate full Kyber + Dilithium + Falcon bundle |
| `kyber_keygen()` | KEM key pair generation |
| `kyber_encapsulate()` | Encrypt shared secret |
| `kyber_decapsulate()` | Decrypt shared secret |
| `dilithium_sign()` | Post-quantum signing |
| `dilithium_verify()` | Post-quantum signature verification |
| `falcon_sign()` | Compact post-quantum signing |
| `falcon_verify()` | Compact signature verification |

### 4.3 Quantum Vault Encryption

The vault uses AES-256-CTR for data encryption with HMAC-SHA256 for integrity:

```python
# From _encrypt_data
cipher = Cipher(algorithms.AES(key), modes.CTR(iv))
encryptor = cipher.encryptor()
hmac = hmac.new(hmac_key, encrypted_data, "sha256").hexdigest()
```

---

## 5. Hardware Security

### 5.1 Hardware Backend Abstraction

Defined in [`core/security/hardware_hard_lock.py`](../../core/security/hardware_hard_lock.py). The [`HardwareBackend`](../../core/security/hardware_hard_lock.py:50) ABC defines:

| Method | Purpose |
|--------|---------|
| [`seal()`](../../core/security/hardware_hard_lock.py:58) | Encrypt data bound to the device |
| [`unseal()`](../../core/security/hardware_hard_lock.py:72) | Decrypt sealed data |
| [`sign()`](../../core/security/hardware_hard_lock.py:86) | Sign a digest |
| [`verify()`](../../core/security/hardware_hard_lock.py:99) | Verify a signature |
| [`get_process_list()`](../../core/security/hardware_hard_lock.py:113) | Enumerate running processes |
| [`get_network_connections()`](../../core/security/hardware_hard_lock.py:123) | Enumerate active connections |
| [`get_tpm_info()`](../../core/security/hardware_hard_lock.py:133) | Query TPM capabilities |

Two implementations:

| Backend | Algorithm | Key Source |
|---------|-----------|------------|
| [`SoftwareBackend`](../../core/security/hardware_hard_lock.py:144) | AES-256-CTR + HMAC-SHA256 | Machine-local seed derived from hostname + MAC |
| [`TPMBackend`](../../core/security/hardware_hard_lock.py:309) | tpm2-pytss or subprocess | Hardware TPM 2.0 |

### 5.2 Hardware Hard Lock

The [`HardwareHardLock`](../../core/security/hardware_hard_lock.py:513) class provides continuous threat monitoring:

```mermaid
flowchart TD
    subgraph Monitoring
        FI[File Integrity Scanning]
        PA[Process Anomaly Detection]
        NT[Network Threat Detection]
        TA[TPM Attestation]
    end
    subgraph Detection
        TC[Threat Confidence Calculation]
        TL[Threat Level Determination]
        AV[Attack Vector Identification]
    end
    subgraph Response
        HL[Hard Lock Execution]
        FA[Forensic Report]
        SC[Sovereign Council Notification]
        HA[Hack Attempt Logging]
    end
    FI --> TC
    PA --> TC
    NT --> TC
    TA --> TC
    TC --> TL
    TL --> HL
    HL --> FA
    HL --> SC
    HL --> HA
```

**Threat levels** ([`ThreatLevel`](../../core/security/hardware_hard_lock.py:462)): `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`

**Hardware states** ([`HardwareState`](../../core/security/hardware_hard_lock.py:471)): `NORMAL`, `COMPROMISED`, `LOCKED`, `RECOVERING`

### 5.3 Tamper Evidence

- **File integrity**: SHA-256 snapshots compared on each scan cycle
- **Process monitoring**: Detects unauthorized debuggers, code injectors, keyloggers
- **Network monitoring**: Detects unauthorized connections, port scanning, DNS tunneling
- **Government attack detection**: Tier-2 pattern matching for state-level threats

---

## 6. OS Control Sandbox

Defined in [`core/orchestrator/tools/sandbox/docker_sandbox.py`](../../core/orchestrator/tools/sandbox/docker_sandbox.py). The [`DockerSandbox`](../../core/orchestrator/tools/sandbox/docker_sandbox.py:40) provides hardened execution for high-risk operations:

### 6.1 Trusted Image Allowlist

```python
TRUSTED_IMAGES = {
    "python:3.11-slim",
    "python:3.10-slim",
    "alpine:3.19",
    "ubuntu:24.04",
    "busybox:stable",
}
```

### 6.2 Container Hardening

The [`_prepare_container_config()`](../../core/orchestrator/tools/sandbox/docker_sandbox.py:151) method applies the following security constraints:

| Setting | Value | Purpose |
|---------|-------|---------|
| `read_only` | `true` | Read-only root filesystem |
| `security_opt` | `no-new-privileges:true` | Prevent privilege escalation |
| `user` | UID 1000 (non-root) | Low-privilege user |
| `cap_drop` | `ALL` | Drop all Linux capabilities |
| `mem_limit` | `512m` | Memory ceiling |
| `cpu_count` | 1.0 | CPU limit |
| `network_mode` | `none` (for scripts) | Network isolation |
| `tmpfs` | `/tmp:noexec,nosuid,size=100m` | Secure temp storage |

### 6.3 Command Sanitization

The [`_sanitize_command()`](../../core/orchestrator/tools/sandbox/docker_sandbox.py:68) method rejects dangerous patterns (`rm -rf /`, `sudo`, shell=True patterns, pipe bombs).

---

## 7. Audit Trail

Defined in [`core/security/audit_log.py`](../../core/security/audit_log.py). The [`AuditLog`](../../core/security/audit_log.py:55) provides tamper-evident logging:

### 7.1 Event Types

| Event Type | Severity | Example |
|------------|----------|---------|
| `AUTHENTICATION` | INFO/WARNING | Login success/failure |
| `AUTHORIZATION` | INFO | Permission grant/deny |
| `DATA_ACCESS` | INFO | User data read |
| `DATA_MODIFICATION` | WARNING | Data create/update/delete |
| `CONFIGURATION_CHANGE` | WARNING | Security policy update |
| `SYSTEM_EVENT` | INFO | Service start/stop |
| `SECURITY_ALERT` | ERROR/CRITICAL | Intrusion detected |

### 7.2 Log Entry Schema

```python
@dataclass
class AuditLogEntry:
    timestamp: str           # ISO 8601
    event_type: AuditEventType
    severity: AuditSeverity
    agent_id: str
    action: str
    resource: str
    status: str              # success / failure / blocked
    details: Dict
    checksum: str            # SHA-256 of previous entry (blockchain chain)
    previous_hash: str
```

### 7.3 Key Operations

| Method | Purpose |
|--------|---------|
| [`log_event()`](../../core/security/audit_log.py:72) | Record an audit event |
| [`query_logs()`](../../core/security/audit_log.py:119) | Search audit trail by filters |
| [`get_entry()`](../../core/security/audit_log.py:173) | Retrieve single entry by ID |
| [`cleanup_old_entries()`](../../core/security/audit_log.py:198) | Prune expired entries |
| [`get_stats()`](../../core/security/audit_log.py:214) | Audit log statistics |

### 7.4 Consensus Audit Trail

Consensus decisions are independently logged to `consensus_audit.jsonl` by the [`ConsensusEngine`](../../core/consensus/consensus_engine.py) for cross-referencing with the security audit log.

---

## 8. Anomaly Detection & Incident Response

### 8.1 Kill Switch

The security middleware in [`core/security/auth_middleware.py`](../../core/security/auth_middleware.py) provides kill switch functionality:

- Records the kill event in the audit log
- Triggers immediate sandbox rollback
- Notifies all registered security handlers
- Requires `top_secret` level to re-arm

### 8.2 Checkpoints

The security system supports named checkpoints for state recovery:

- `create_checkpoint(name)`: Snapshot current security posture
- `rollback_to_checkpoint(id)`: Restore to previous safe state

### 8.3 Anomaly Types

| Type | Detection Signal |
|------|------------------|
| `RAPID_FIRE` | >100 actions in 60s from same agent |
| `ABNORMAL_SEQUENCE` | Unusual action ordering |
| `ESCALATION` | Repeated denied access attempts |
| `PATTERN_MATCH` | Known attack pattern signature |

---

## 9. Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OVERRIDE_TTL` | `600` | Override request TTL (seconds) |
| `AUDIT_MAX_ENTRIES` | `10000` | Max audit log entries before cleanup |
| `FINAL_THREE_DECISIONS` | `3` | Auto-override trigger count |
| `QUORUM_TIMEOUT` | `300` | Quorum waiting period (seconds) |
| `PQC_PROVIDER` | `"software_fallback"` | PQC implementation backend |

---

## 10. Security Test Coverage

| Test File | Focus | Lines |
|-----------|-------|-------|
| [`tests/security/test_jwt.py`](../../tests/security/test_jwt.py) | JWT auth, login, session management | — |
| [`tests/security/test_blockchain_identity_advanced.py`](../../tests/security/test_blockchain_identity_advanced.py) | Blockchain identity, DID, VC | — |
| [`tests/security/test_zkp_comprehensive.py`](../../tests/security/test_zkp_comprehensive.py) | Zero-Knowledge Proof verification | — |
| [`tests/security/test_mythos_scanner.py`](../../tests/security/test_mythos_scanner.py) | Mythos threat scanner | — |
| [`tests/security/test_security_production.py`](../../tests/security/test_security_production.py) | Production security hardening | — |
| [`tests/real/test_monitoring_security.py`](../../tests/real/test_monitoring_security.py) | Monitoring & security middleware | — |

---

## References

- [`core/security/auth_middleware.py`](../../core/security/auth_middleware.py) — Auth middleware & access control
- [`core/security/biometric_hardware_gate.py`](../../core/security/biometric_hardware_gate.py) — Level-3 biometric gate
- [`core/security/post_quantum_crypto.py`](../../core/security/post_quantum_crypto.py) — PQC stubs + quantum vault
- [`core/security/hardware_hard_lock.py`](../../core/security/hardware_hard_lock.py) — Hardware backend + hard lock
- [`core/security/audit_log.py`](../../core/security/audit_log.py) — Tamper-evident audit trail
- [`core/orchestrator/tools/sandbox/docker_sandbox.py`](../../core/orchestrator/tools/sandbox/docker_sandbox.py) — Docker sandbox hardening
- [`core/security/jwt.py`](../../core/security/jwt.py) — JWT authentication
- [`core/consensus/consensus_engine.py`](../../core/consensus/consensus_engine.py) — Domain veto registry
- [`core/security/zkp.py`](../../core/security/zkp.py) — Zero-Knowledge Proof system
- [`core/security/immutable_constitution.py`](../../core/security/immutable_constitution.py) — Immutable constitution
- [`core/security/power_balance_constitution.py`](../../core/security/power_balance_constitution.py) — Power balance 51/49
