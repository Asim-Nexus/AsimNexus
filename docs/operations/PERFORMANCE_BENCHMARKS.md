# Performance Benchmarks — v1.0.1
Date: 2026-06-01

## Mesh Layer

| Operation | Avg | p95 | Samples |
|-----------|-----|-----|---------|
| P2PMessage round-trip | 17.24 µs | 24.10 µs | 10000 |
| DHT find_closest_nodes (100 nodes) | 53.01 µs | 76.40 µs | 10000 |
| CRDT GCounter increment+value | 4.31 µs | 5.00 µs | 10000 |

## Consensus Layer

| Operation | Avg | p95 | Samples |
|-----------|-----|-----|---------|
| Consensus majority vote (15 voters) | 39.29 µs | 46.10 µs | 10000 |

## Security Layer

| Operation | Avg | p95 | Samples |
|-----------|-----|-----|---------|
| Security Level-3 check_access (mocked) | 542.46 µs | 969.30 µs | 500 |

## Startup

| Operation | Avg | p95 | Samples |
|-----------|-----|-----|---------|
| Import all major modules (5 modules) | 16063.60 µs | 16063.60 µs | 1 |

## Memory

| Operation | Avg | p95 | Samples |
|-----------|-----|-----|---------|
| Memory footprint (key data structures) | 768.00 µs | 768.00 µs | 1 |

---

### Notes
- Benchmarks run on developer machine; results are relative, not absolute.
- Slow operations (>100ms avg) flagged with ⚠️ as potential optimization targets for v1.2.
- All benchmarks run with 10,000 iterations (except startup time and memory).

