# Security Framework

> **Biometric gates, hardware locks, and threat detection for Digital Nepal**

## Overview

The AsimNexus security framework implements a multi-layered defense system that protects citizen data, enterprise operations, and government infrastructure. The framework combines biometric verification, hardware-level security, and continuous threat monitoring.

## Layer 1: Biometric Hardware Gate

### Purpose

The Biometric Hardware Gate (`core/security/biometric_hardware_gate.py`) provides hardware-backed biometric verification for critical system operations.

### States

| State | Description |
|-------|-------------|
| `DISARMED` | Normal operation, no active threats |
| `ARMING` | Threat detected, gate preparing to lock |
| `ARMED` | Gate locked, biometric verification required |
| `VERIFYING` | Biometric verification in progress |
| `GRANTED` | Verification successful, access granted |
| `DENIED` | Verification failed, access denied |
| `BYPASSED` | Emergency bypass activated |
| `ERROR` | System error, fail-safe mode |

### Verification Process

1. Threat detected → Gate arms
2. User provides biometric data (fingerprint, face, voice)
3. System verifies against registered templates
4. If matched → Access granted
5. If not matched → Access denied, attempt logged
6. After 3 failed attempts → Gate escalates to admin

### Emergency Bypass

In genuine emergencies, authorized personnel can bypass the biometric gate using:
- Multi-factor override codes
- Hardware security keys
- Constitutional Council authorization

## Layer 2: Hard Lock Security

### Purpose

Hard Lock Security (`core/security/hard_lock.py`) provides encryption-based access control for sensitive data and operations.

### Lock Types

| Type | Description | Use Case |
|------|-------------|----------|
| `SOFT` | Software-based encryption | Standard data protection |
| `HARD` | Hardware-backed encryption | Sensitive data |
| `QUANTUM` | Quantum-resistant encryption | Classified data |
| `BIO` | Biometric-bound encryption | Personal data |

### Encryption Levels

| Level | Algorithm | Key Length |
|-------|-----------|:----------:|
| Standard | AES-256-GCM | 256-bit |
| High | AES-256-GCM + HMAC-SHA256 | 512-bit |
| Quantum | Kyber-1024 + AES-256-GCM | Post-quantum |
| Maximum | Multi-layer with hardware binding | Custom |

### Access Control

1. **Request** — User requests access to locked resource
2. **Verification** — System verifies user identity and permissions
3. **Decryption** — Resource is decrypted for authorized access
4. **Audit** — Access is logged with timestamp and user ID
5. **Re-lock** — Resource is re-encrypted after access

## Layer 3: Hardware Hard Lock

### Purpose

Hardware Hard Lock (`core/security/hardware_hard_lock.py`) provides the highest level of security with hardware-backed threat detection and response.

### Threat Levels

| Level | Score | Response |
|-------|:-----:|----------|
| `LOW` | 0-25 | Log and monitor |
| `MEDIUM` | 26-50 | Alert administrators |
| `HIGH` | 51-75 | Activate additional monitoring |
| `CRITICAL` | 76-100 | Execute hard lock protocol |

### Detection Capabilities

1. **Process Anomalies** — Detect unauthorized processes
2. **Network Threats** — Detect suspicious network connections
3. **File Integrity** — Monitor critical file changes
4. **TPM Attestation** — Verify hardware integrity via TPM
5. **Government Attack Detection** — Detect state-level attacks

### Hard Lock Protocol

When a CRITICAL threat is detected:

1. **Immediate Lock** — All sensitive operations are locked
2. **Biometric Gate Arms** — Biometric verification required
3. **Forensic Snapshot** — System state is captured for analysis
4. **Sovereign Council Notification** — Council is alerted
5. **Audit Trail** — Full incident report is generated
6. **Recovery** — Gradual restoration after threat neutralized

## Layer 4: Continuous Monitoring

### File Integrity Monitoring

The system continuously monitors critical files for unauthorized changes:

- System configuration files
- Security policy files
- Contract database
- Audit logs
- Constitutional documents

### Process Monitoring

The system monitors running processes for:

- Unauthorized processes
- Suspicious behavior patterns
- Resource abuse
- Privilege escalation attempts

### Network Monitoring

The system monitors network connections for:

- Unauthorized connections
- Data exfiltration attempts
- Man-in-the-middle attacks
- DNS spoofing
- Port scanning

## Security Test Coverage

The security framework is validated by 80 comprehensive tests:

| Test Suite | Tests | Status |
|------------|:-----:|:------:|
| `test_blockchain_identity_advanced.py` | 15 | ✅ All Pass |
| `test_jwt.py` | 12 | ✅ All Pass |
| `test_mythos_scanner.py` | 18 | ✅ All Pass |
| `test_security_production.py` | 20 | ✅ All Pass |
| `test_zkp_comprehensive.py` | 15 | ✅ All Pass |

## Implementation

The security framework is implemented in:

- [`core/security/biometric_hardware_gate.py`](../core/security/biometric_hardware_gate.py) — Biometric gate
- [`core/security/hard_lock.py`](../core/security/hard_lock.py) — Hard lock security
- [`core/security/hardware_hard_lock.py`](../core/security/hardware_hard_lock.py) — Hardware hard lock
- [`core/security/power_balance_constitution.py`](../core/security/power_balance_constitution.py) — Power balance enforcement
- [`tests/security/`](../tests/security/) — Security test suites
