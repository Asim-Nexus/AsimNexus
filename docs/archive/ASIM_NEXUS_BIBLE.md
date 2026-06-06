# ASIM_NEXUS_BIBLE.md
# AsimNexus — Dharma-Chakra MAOS
# Version 4.1 — Honest Architecture, Real Code, Real Roadmap
# "Machine works. Human decides. Always."
# जय धर्मचक्र ⚖️

---

## TABLE OF CONTENTS

1. [Vision — What AsimNexus Is](#1-vision)
2. [Reality Check — What Exists NOW vs Planned](#2-reality-check)
3. [Core Philosophy — Dharma-Chakra](#3-core-philosophy)
4. [Architecture — 5 Immutable Layers](#4-architecture)
5. [ΔT Engine — Mathematical Model + Code Reference](#5-delta-t-engine)
6. [Quad-System Mesh — Realistic Path](#6-mesh-protocol)
7. [15 Founder Clones](#7-founder-clones)
8. [Human Digital Twin + ZKP Confirmation](#8-human-digital-twin)
9. [Anti-Concentration Mechanisms](#9-anti-concentration)
10. [Universal Chatbox — Primary Interface](#10-universal-chatbox)
11. [Implementation Roadmap Phase 1→4](#11-roadmap)
12. [File Structure](#12-file-structure)
13. [How to Run Now](#13-how-to-run)

---

## 1. VISION — WHAT ASIMNEXUS IS

AsimNexus is a **World Operating System** — not a product, not an app, not a company.

### The Problem It Solves

BlackRock, Vanguard, State Street — 3 companies hold major stakes in 90%+ of the world's
largest corporations. ~$20 trillion controls media narratives, ESG policy, national debt
conditions, and government decisions. Nobody voted for this. Nobody can audit it.
Nobody can exit it.

This is **Hyper-Centralized Corporatocracy**:
- Invisible control through financial ownership
- ESG as a tool to impose foreign agendas on sovereign nations
- Media ownership ensuring narrative compliance
- Debt as leverage to control national policy
- "Universal Standards" that erase local culture and sovereignty

### The Answer: Distributed Sovereign Power

AsimNexus makes this impossible — technically, mathematically, constitutionally:

```
Every person owns their own Universe.
No entity can hold >5-8% of network influence.
All critical decisions require human confirmation.
Data lives on the owner's device. Always.
Machine proposes. Human decides. Period.
```

### The Three Universe Layers

AsimNexus is not one system — it is a **living Mesh Local Cloud** made of sovereign universes:

```
┌─────────────────────────────────────────────────────────┐
│  PERSONAL UNIVERSE                                      │
│  Every person's own life, family, work, data, clone.    │
│  Runs on their own device. Nobody else can enter.       │
├─────────────────────────────────────────────────────────┤
│  ENTERPRISE UNIVERSE                                    │
│  Every company's own operations, agents, contracts.     │
│  Governed by Dharma rules. ΔT-capped influence.         │
├─────────────────────────────────────────────────────────┤
│  SOVEREIGN UNIVERSE                                     │
│  Every government/nation's policy, data, law.           │
│  Air-gap capable. Emergency isolation built-in.         │
└─────────────────────────────────────────────────────────┘
         ALL CONNECTED via Quad-Mesh
         NONE controlling the other
         EACH sovereign and self-healing
```

### How It Actually Works (Concrete Flow)

```
1. Farmer needs help with harvest logistics
   → Posts request via Universal Chatbox
   → AsimNexus scans mesh for matching skills

2. Another person has matching skills + Agent Mode ON
   → Their Clone proposes a Smart Contract (5/15/30 days)
   → Both parties receive Final 3 Confirmation prompt

3. Human-in-the-Loop (mandatory):
   → Logical Check (AI validates contract terms)
   → Dharma Check (local law + culture compliance)
   → Human Sign-Off (YOU confirm — cannot be skipped)

4. Work happens. Clone executes. Human monitors.
5. Completion: both confirm. Payment released from escrow.
6. Dreaming Engine consolidates memory. Mesh rebalances.
```

### Mesh Local Cloud — Resource Sharing

```
Every device contributes 2-5% of idle resources (with consent):
  - CPU cycles when screen off
  - RAM headroom
  - Storage for encrypted local data shards

Offline:  Local Mesh (home/village/city) runs independently.
Online:   Delta Sync — only changes, never full data.
Emergency: Air-Gap mode — entire community exits global mesh,
           runs fully local until safe to reconnect.
```

### Core Mantra

> "प्रविधि मानिसको दास हो, मालिक होइन।"
> Technology is humanity's servant — never its master.

> "जय धर्मचक्र — मशिनले काम गर्छ, मानिसले निर्णय गर्छ।"

---

## 2. REALITY CHECK — WHAT EXISTS NOW vs WHAT IS PLANNED

**⚠️ IMPORTANT: ~90% of the grand vision is currently architecture design, not working code.
This is NORMAL. Every civilization starts with a seed. Honesty here prevents wasted effort.**

### ✅ WORKING TODAY (c:\AsimNexus)

| Component | File | What it actually does |
|-----------|------|-----------------------|
| Backend API | `simple_backend.py` | FastAPI, SQLite, auth, chat, jobs |
| Local LLM | `connectors/unified_llm_gateway.py` | Qwen3 GGUF — offline inference |
| 15 Clone routing | `core/founder_clones/world_clones.py` | Role-based prompt routing |
| Memory store | SQLite in `simple_backend.py` | Chat history save/retrieve |
| Job marketplace | `core/economy/job_marketplace.py` | Post/apply/rate jobs |
| Dreaming engine | `core/dreaming/dreaming_engine.py` | Background memory summaries |
| React frontend | `frontend/react/src/` | Full UI running on localhost:3000 |
| Chat UI | `UniversalChat.jsx` | Conversational interface |
| Dashboard | `Dashboard.js` | Real CPU/RAM metrics |
| Memory browser | `MemoryPage.jsx` | Browse, search, delete memories |
| WorldClones UI | `WorldClones.jsx` | 15 clones grid + chat |
| Settings page | `SettingsPage.jsx` | API keys, profile, system info |

### 🔲 PLANNED — NOT YET CODE

| Concept | Current State | Phase to Build |
|---------|---------------|----------------|
| ΔT Engine v2 | **WORKING CODE** — `core/dharma/delta_t_engine.py` | ✅ Done Phase 1 |
| Personal/Enterprise/Sovereign Universe layers | Architecture defined | Phase 2 |
| P2P LAN Mesh | Single machine only | Phase 2 |
| 2-5% Resource Sharing with consent | Not coded | Phase 2 |
| Delta Sync (offline-first) | Not coded | Phase 2 |
| Real ZKP Crypto | UI button placeholder | Phase 2 |
| Dharma Veto (enforced) | Concept only | Phase 2 |
| Anti-Monopoly enforcement | Not coded | Phase 2 |
| Human Digital Twin (full) | User profile only | Phase 3 |
| Air-Gap Mode | Not coded | Phase 3 |
| Community Mesh | Not coded | Phase 3 |
| Sovereign Micro-tokens | Not coded | Phase 4 |
| 15 specialized models | 1 Qwen3 + routing | Phase 4 |
| Cultural Sovereignty Compiler | Concept only | Phase 3 |
| Global Mesh | Single machine | Phase 4 |

---

## 3. CORE PHILOSOPHY — DHARMA-CHAKRA

### The Four Immutable Laws (AI cannot override these)

**Law 1 — Human Supremacy**
No AI decision is ever final. Every critical action requires
human confirmation before execution. The human is always the axis.

**Law 2 — Anti-Concentration**
No single entity — person, company, government, AI — may hold
more than 5-8% of total network influence, resources, or decision power.
This is enforced by the ΔT Engine mathematically.

**Law 3 — Local-First Privacy**
- Primary mode: Local machine only
- Second mode: LAN mesh (trusted devices)
- Third mode: Community mesh (opted-in nodes)
- Cloud: Last resort only. Minimum data. Always encrypted.
- No central server. Ever.

**Law 4 — Cultural Sovereignty**
"Universal Standards" imposed from outside are filtered through
local cultural context. Foreign agenda ≠ automatic acceptance.
Communities define their own rules within the Dharma framework.

### Why Dharma-Chakra?

The Dharma Chakra (धर्मचक्र) has 24 spokes — 24 spokes of righteous law.
In AsimNexus: 24 ethical constraints baked into the kernel.
The wheel spins (system operates) only with a human at the center.
Remove the human → wheel stops.

### The Problem with BlackRock-Style Systems

```
BlackRock System:          AsimNexus:
─────────────────          ──────────
Central control    →       Distributed sovereignty
ESG as weapon      →       Cultural context compiler
Debt leverage      →       Local asset-backed economy
Narrative control  →       Cognitive firewall
Invisible power    →       Transparent ΔT measurement
One global rule    →       Local rules + global ethics
```

---

## 4. ARCHITECTURE — 5 IMMUTABLE LAYERS

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 5: OMNI-OPERATOR INTERFACE                               │
│  Universal Chatbox (PRIMARY) + Dashboard + Clones + Memory      │
│  Everything accessible through conversation                     │
│  React Frontend — localhost:3000                                │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 4: AGENTIC MATRIX                                        │
│  15 Founder Clones — domain specialists                         │
│  Human Digital Twins — Agent Mode ON/OFF                        │
│  Job Marketplace — 5/15/30 day skill contracts                  │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 3: DHARMA-CHAKRA GUARD  ← IMMUTABLE KERNEL              │
│  ΔT Engine — Influence measurement + Auto-limit                 │
│  Cultural Sovereignty Compiler                                  │
│  ZKP Level-3 Human Confirmation Valve                           │
│  Dharma Veto — blocks anti-sovereignty actions                  │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 2: MESH NETWORK                                          │
│  Personal (local machine) → LAN P2P → Community → Global       │
│  2% → 3% → 4% → 5% resource sharing (consent-based)           │
│  Emergency Air-Gap mode                                         │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 1: PURE KERNEL                                           │
│  FastAPI Backend — simple_backend.py                            │
│  Local LLM — Qwen3 GGUF (works offline)                        │
│  SQLite → PostgreSQL → Distributed DB (as it grows)            │
│  WebSocket — real-time metrics                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Design Principle:** Each layer is independent. Layer 1 works without Layer 2.
Layer 2 works without Layer 4. The system degrades gracefully.
Local always works. Cloud is optional.

---

## 5. ΔT ENGINE — MATHEMATICAL MODEL + CODE REFERENCE

### What It Does

Continuously measures the influence/power of every node in the network.
Detects concentration. Auto-limits before monopoly forms.
Enforces the 5-8% cap mathematically — no manual intervention needed.

### The Math

**Node Influence Formula:**

    P_i(t) = α·W_R(t) + β·V_I(t) + γ·C_R(t)

Where:
```
P_i(t)  = Total influence of node i at time t
W_R(t)  = Resource Weight
           (CPU%, RAM%, storage%, assets held — normalized 0.0 to 1.0)
V_I(t)  = Interaction Velocity
           (transactions/sec, messages/sec — normalized 0.0 to 1.0)
C_R(t)  = Reputation Centrality
           (decentralized reputation index — normalized 0.0 to 1.0)

α, β, γ = weighting coefficients, must sum to 1.0
           Default: α=0.4, β=0.3, γ=0.3
```

**Dynamic Influence Cap:**

    P_i(t) ≤ L_max × P_total(t)

    L_max = 0.05 to 0.08  (5-8% of total network influence)
    Default L_max = 0.07 (7%)

**Symmetry Attenuation (Auto-Reduction):**

When P_i exceeds L_max, the node's effective power is attenuated:

    P_effective_i = P_i × e^( −λ × max(0, P_i − L_max × P_total) )

    λ = attenuation aggression factor (default: 10.0)

The exponential decay means: the more a node tries to dominate,
the faster and harder it is pushed back. Self-correcting.

**ΔT Score (deviation from balance):**

    ΔT_i = P_i(t) − (P_total(t) / N)

    N = total number of active nodes
    ΔT_i > 0 → node has more than fair share → attenuation applies
    ΔT_i < 0 → node is below fair share → no action

**Dharma Veto Trigger:**

    IF P_i > L_max × P_total:
        TRIGGER veto_event(node_id=i, severity=ΔT_i)
        NOTIFY user
        APPLY attenuation
        LOG to audit trail

### Code Reference

```
File:   core/dharma/delta_t_engine.py   ← BUILD THIS (Phase 1)
Class:  DeltaTEngine
Methods:
  add_node(node_id, alpha, beta, gamma)
  update_node(node_id, resource_weight, interaction_velocity, reputation)
  compute_influence(node_id) → float
  compute_total_influence() → float
  check_cap(node_id) → (bool, float)   # (violated, delta_t_score)
  apply_attenuation(node_id) → float   # returns effective power
  run_cycle() → list[VetoEvent]        # full network scan
```

**Simulation:**
```
core/dharma/simulate_dt.py  ← Run to see ΔT Engine in action
python -m core.dharma.simulate_dt
```

### Dharma Veto Logic

```python
IF incoming_protocol in ["Global_Standard", "External_Policy"]:
    run contextual_dharma_compiler(local_context)

    IF local_resource_control < 1.0 OR data_drain_rate > 0:
        status = "SOVEREIGNTY_INVASIVE"
    ELIF cultural_value_deviation:
        status = "CULTURAL_ANOMALY"
    ELSE:
        status = "COMPLIANT"

    IF status != "COMPLIANT":
        TRIGGER dharma_veto()
        ALERT user: "External agenda detected. 3-step confirmation required to allow."
    ELSE:
        PROCEED to final_3_confirmation()
```

---

## 5.5 COMPLEX MATHEMATICS LAYER — i² = -1 POWERS ASIMNEXUS

### Why Complex Numbers?

Complex numbers (z = x + iy, where i² = -1) are the invisible heart of modern computing.
They capture both magnitude and phase in a single elegant form. AsimNexus harnesses
this power across all subsystems.

```
i² = -1
z = x + iy = r·e^(iθ)
|z| = √(x² + y²)     ← magnitude (energy, signal strength)
θ = atan2(y,x)       ← phase (timing, resonance)
```

### Implemented Complex Modules

#### 1. core/math/complex_engine.py
The mathematical foundation:
- `ComplexNumber`: z = x + iy with full arithmetic
- `SignalProcessor`: FFT using complex exponentials O(n log n)
- `Quaternion`: 3D rotations for spatial computing
- `WavePropagation`: ψ = A·e^(i(k·r - ωt))
- `QuantumState`: |ψ⟩ = α|0⟩ + β|1⟩ with complex amplitudes
- `ComplexNeuralNetwork`: Complex-valued weights and activations
- `DeltaTEngine`: z = E + i·S (Energy + i·Entropy)
- `FractalGenerator`: z² + c iteration for visualization
- `PostQuantumCrypto`: Lattice-based encryption

#### 2. core/brain/dreaming_complex.py
Complex-valued dreaming engine:
- Neural networks with complex weights
- Phase-based pattern recognition
- Oscillation detection in time-series
- FFT spectral analysis of patterns

#### 3. core/timeflow/delta_t_complex.py + advanced_delta_complex.py
Energy flow on complex plane:
```
z = E + i·S
where E = Net energy flow (real)
      S = Entropy generation (imaginary)

Trajectory analysis:
- dz/dt = velocity on complex plane
- d²z/dt² = acceleration
- Fractal dimension of flow patterns
- FFT-based resonance detection
- Neural network predictions
```

#### 4. core/mesh/wave_propagation_mesh.py + full_wave_simulation.py
Wireless signal simulation:
```
ψ(x,y,t) = Σ (Aₙ/rₙ) · exp(i(kₙrₙ - ωₙt))

k = 2π/λ = 2πf/c  (wave number)
λ = c/f           (wavelength at 2.4GHz = 12.5cm)

Features:
- 2D wave equation simulation
- Multi-frequency (2.4GHz, 5GHz)
- Obstacle attenuation modeling
- Interference patterns
- Optimal node placement algorithm
```

#### 5. core/visualization/fractal_universe.py
Dashboard visualizations:
- Mandelbrot set: z → z² + c
- Julia sets: fixed c, varying z₀
- Buddhabrot: probability density visualization
- Real-time rendering (400x300 @ 30fps)
- Health-based color schemes

#### 6. core/quantum/quantum_bridge_complex.py
Quantum-ready cryptography:
```
|ψ⟩ = α|0⟩ + β|1⟩
P(|0⟩) = |α|², P(|1⟩) = |β|²

Features:
- Qubit superposition simulation
- Entanglement: |Φ⁺⟩ = (|00⟩ + |11⟩)/√2
- Quantum teleportation protocol
- QKD (Quantum Key Distribution) BB84
- Post-quantum lattice encryption
- Quantum random number generation
```

#### 7. core/signal/signal_processing_module.py
FFT-based signal processing:
```
Voice Processing:
- Pitch detection via FFT peak
- Formant extraction (F1, F2, F3)
- MFCC coefficients
- Noise reduction (spectral subtraction)
- Command detection

Video Processing:
- Motion detection (phase correlation)
- Frame compression (frequency domain)

Medical Sensors:
- ECG: Heart rate & arrhythmia detection
- Accelerometer: Activity recognition

Radar:
- Doppler shift analysis
- Range detection
```

### Asim Orb Complex Integration

The floating chat interface now includes:
- Live fractal background (Mandelbrot z² + c)
- Wave propagation visualization (mesh interference)
- FFT spectrum analyzer (voice input)
- Voice-activated mode switching (Alt+V)
- Real-time pitch and energy display

### Backend API Endpoints

```python
# Complex Engine Integration
POST /api/complex/fft           # FFT of signal data
POST /api/complex/wave          # Wave propagation at point
POST /api/complex/mandelbrot    # Render fractal region
POST /api/complex/quantum/qkd   # Simulate QKD protocol

# DeltaT Advanced
POST /api/deltat/record         # Record complex flow
GET  /api/deltat/analysis/{source}  # Advanced analysis
GET  /api/deltat/resonance/{source} # Detect resonance
GET  /api/deltat/predict/{source}   # Neural predictions

# Mesh Wave Simulation
POST /api/mesh/simulate       # Run wave simulation
GET  /api/mesh/heatmap        # Get quality heatmap
POST /api/mesh/optimal-placement  # Find best node positions
GET  /api/mesh/signal-at/{x}/{y}   # Signal at location
```

### Mathematical Power Summary

```
i² = -1 enables:
├── Signal Processing: FFT converts time ↔ frequency
├── Dreaming: Complex neural networks detect oscillations
├── Energy: z = E + i·S models efficiency on complex plane
├── Mesh: Wave equation optimizes wireless topology
├── Quantum: |ψ⟩ = α|0⟩ + β|1⟩ simulates quantum security
├── Fractals: z² + c creates infinite complexity from simplicity
└── Visuals: Beautiful math powers Asim Orb backgrounds
```

---

## 6. QUAD-SYSTEM MESH — REALISTIC PATH

**Key principle: Local-First always. Cloud is the last resort.**

### Realistic Growth Path (not theory — actual build order)

```
Stage 0 — NOW (done):
  Single machine. Backend + Frontend on localhost.
  No networking beyond this machine.

Stage 1 — Phase 2 (LAN P2P):
  2-3 machines on same WiFi/LAN discover each other.
  mDNS multicast → ZKP auth → consent → join.
  2% resource sharing (CPU/RAM).
  All data stays on local machines.

Stage 2 — Phase 3 (Community Mesh):
  Multiple homes/offices → trusted mesh.
  Kademlia DHT for routing.
  3-4% resource sharing.
  Emergency Air-Gap: disconnect from global, run local only.

Stage 3 — Phase 4 (Sovereign + Global Mesh):
  Full distributed mesh.
  5% max resource sharing.
  National-level nodes possible.
  No central server ever.
```

### 4-Level Architecture (eventual)

```
Level 4: Global Quad Mesh          5% max  (Phase 4)
         ↑↓ Regional Bootstrap Nodes
Level 3: Sovereign Mesh            4%      (Phase 3 - orgs/govts)
         ↑↓ Federated Tree + Cross-Links
Level 2: Community Mesh            3%      (Phase 3 - neighborhoods)
         ↑↓ Kademlia DHT + LAN Multicast
Level 1: Personal Mesh             2%      (Phase 2 - your devices)
         ↑↓ mDNS + ZKP Auth
Level 0: Single Machine            0%      (NOW - working today)
```

### Resource Sharing Rules

- **Consent-based**: User controls 0-5% slider. Default: OFF.
- **Sandboxed**: Shared resources cannot access private data.
- **Priority Queue**: Personal > Community > Sovereign > Global
- **Reward**: Sharing earns Reputation Score (feeds C_R in ΔT Engine)
- **Revocable**: User can withdraw at any time instantly.

### Emergency Air-Gap Mode

```
Trigger: User types "Emergency Air-Gap" in Chat
         OR ΔT detects external attack pattern

Actions:
  1. All external connections → BLOCKED instantly
  2. Local Mesh → 100% autonomous operation continues
  3. Decisions queue with timestamp + local ZKP proof
  4. Re-sync → when re-connecting, ZKP + Dharma check on queued items

File to build: core/mesh/air_gap_controller.py (Phase 3)
```

---

## 7. THE 15 FOUNDER CLONES

Each clone is a **specialist AI role** — not a separate model today,
but a domain-specific prompt + routing strategy.

**Current reality**: 1 Qwen3 GGUF model + role-based prompting.
**Target**: Route to best available model per domain (local or API).

| # | Clone Role | Domain | Icon |
|---|-----------|--------|------|
| 1 | Tech Architect | Code, Systems, DevOps | 💻 |
| 2 | Strategic Planner | Vision, Risk, Long-term | 🧭 |
| 3 | Financial Oracle | Money, Tax, Investment | 💰 |
| 4 | Legal Guardian | Law, Contracts, Rights | ⚖️ |
| 5 | Health Sage | Medicine, Mental health, Wellness | ❤️ |
| 6 | Education Mentor | Learning, Teaching, Skills | 📚 |
| 7 | Creative Muse | Writing, Art, Design, Music | 🎨 |
| 8 | Research Explorer | Science, Data, Discovery | 🔬 |
| 9 | Security Sentinel | Cyber, Privacy, Threat detection | 🛡️ |
| 10 | Environmental Steward | Climate, Nature, Sustainability | 🌿 |
| 11 | Social Harmonizer | Culture, Community, Relations | 🤝 |
| 12 | Governance Advisor | Policy, Democracy, Ethics | 🏛️ |
| 13 | Innovation Catalyst | Startups, Disruption, Invention | ⚡ |
| 14 | Logistics Master | Operations, Supply chain | 🚚 |
| 15 | Harmony Keeper | Dharma, Ethics, Balance | ☯️ |

### Consensus Mode (Phase 3 goal)

When a complex high-stakes decision arrives:
1. All 15 clones analyze from their domain angle
2. Internal debate cycle → majority or consensus
3. Result + confidence score → shown to human
4. Human applies Final 3 Confirmation before execution

---

## 8. HUMAN DIGITAL TWIN + ZKP CONFIRMATION

### What a Human Digital Twin Is

```
NOT: A fake AI persona
NOT: A bot pretending to be you
IS:  A cryptographically-bound capability mirror

Your HDT can only perform actions that:
  - Match your real-world verified skills
  - You have explicitly authorized
  - Pass Dharma-Chakra filter
  - Received human Final 3 Confirmation
```

### Agent Mode

```
OFF (default): Your twin is dormant. Nothing happens automatically.
ON (explicit):  Your twin is available in the mesh marketplace.
                Skills are matched to incoming job requests.
                You are notified before any contract is accepted.
                You confirm. Then it starts.
```

### Smart Contract Lifecycle

```
Contract Durations:  5-day (task) / 15-day (project) / 30-day (ongoing)

Step 1 — MATCHING
  Requester posts need via Universal Chatbox.
  AsimNexus scans mesh: skill match + availability + Dharma compliance.
  Top 3 candidates proposed to requester.

Step 2 — NEGOTIATION (AI-assisted, human-decided)
  Clone proposes terms: scope, duration, resource commitment.
  Both parties see transparent terms — no hidden clauses.
  ΔT Engine checks: will this concentrate power unfairly?

Step 3 — FINAL 3 CONFIRMATION (both sides)
  Gate 1: AI validates contract legality and feasibility.
  Gate 2: Dharma Compiler checks local law + cultural fit.
  Gate 3: Human on BOTH sides signs (cannot delegate this).

Step 4 — EXECUTION
  Clone works autonomously within agreed scope.
  Human receives progress pings, can pause/cancel anytime.
  Dreaming Engine logs and consolidates work context.

Step 5 — COMPLETION + SETTLEMENT
  Output delivered. Human on receiving side confirms.
  Escrow released. Reputation scores updated on both.
  ΔT Engine rebalances network influence post-contract.

Step 6 — MESH REBALANCE
  Dreaming Engine consolidates memory.
  Network symmetry rechecked via PoS (Proof of Symmetry).
  System self-heals back to balanced state.
```

### What Your Clone CANNOT Do (Dharma Hard Limits)

```
- Cannot sign contracts > 30 days without fresh human confirmation
- Cannot transfer ownership of personal data
- Cannot bypass Final 3 Confirmation under ANY condition
- Cannot work for an entity that has violated ΔT cap
- Cannot operate if your device detects coercion signals
- Cannot be rented to a foreign sovereign without your ZKP approval
```

### Level-3 ZKP Confirmation Valve

**Every critical action must pass 3 gates:**

```
Gate 1 — LOGICAL CHECK
  Who:   AI + Clone assessment
  What:  "Is this technically safe, correct, and beneficial?"
  Pass:  AI confidence score > threshold

Gate 2 — DHARMA CHECK
  Who:   Contextual Dharma Compiler
  What:  "Does this respect local culture, law, sovereignty?"
  Pass:  No Dharma violations detected

Gate 3 — HUMAN SIGN-OFF  ← CANNOT BE SKIPPED
  Who:   You, the human
  What:  Explicit conscious approval
  How:   Biometric (local device) OR ZKP digital signature
  Pass:  You say YES
```

**Nothing executes without all 3 passing. Not even the AI.**

### ZKP Mathematics (simplified)

    Verify(π, V, P) = True/False

```
P  = hash of the proposed action
V  = kernel's public verification key
π  = zero-knowledge proof generated by user's private key
     (computed on LOCAL device — private key never leaves device)

Result: Kernel learns only "approved" or "rejected"
        Never learns WHO approved or their private key
        Works offline — proof generated locally, synced later
```

---

## 9. ANTI-CONCENTRATION MECHANISMS

### How BlackRock-Style Capture Works

```
Step 1: Buy shares in all major companies quietly
Step 2: Use ESG scoring to impose behavioral standards
Step 3: Fund media to control narrative
Step 4: Advise governments (regulatory capture)
Step 5: Control international loans (debt colonialism)
Step 6: "Universal Standards" eliminate local alternatives
Result: Invisible empire. No election. No accountability.
```

### AsimNexus Counter-Mechanisms

**1. ΔT Engine — Mathematical Monopoly Prevention**
Real-time influence tracking. 5-8% cap enforced automatically.
Code: `core/dharma/delta_t_engine.py`

**2. Cultural Sovereignty Layer**
All incoming "global standards" pass through local context compiler.
Local community can override any external rule that violates sovereignty.
Code: `core/dharma/cultural_compiler.py` (Phase 2)

**3. Cognitive Firewall**
Incoming information analyzed for:
- Sponsored narrative signatures
- Bias source identification
- Multi-perspective alternative views shown
No information is suppressed — context is always added.

**4. Sybil Resistance**
Every Human Digital Twin is anchored to:
- Physical biometric (local device)
- Decentralized Reputation Score (earned, not bought)
- Cryptographic identity that cannot be duplicated

**5. National Escape Hatch**
Any community, region, or nation can Air-Gap instantly.
Full local operation. Zero dependency on global mesh.
No permission needed. Instant. Reversible.

**6. Local Asset Economy**
Critical resources (water, energy, food, labor, skills) tokenized locally.
External financial crises cannot collapse local economy.
Barter-compatible fallback always available.

---

## 10. UNIVERSAL CHATBOX — PRIMARY INTERFACE

**The chat IS the OS interface. Everything happens through conversation.**

### Philosophy

Not a feature — the fundamental paradigm.
You don't navigate menus. You talk.
The system routes your intent to the right layer automatically.

### Example Commands (working today)

```
User: "Show me my recent memories"
  → Routes to /memory page + MemoryPage.jsx

User: "Talk to the Legal Guardian clone about my contract"
  → Routes to /clones + selects Legal Guardian

User: "What's my system CPU right now?"
  → Dashboard widget + /api/analytics/overview

User: "Post a job for React developer, 15 days, NPR 5000"
  → Routes to /marketplace + /api/jobs/post
```

### Example Commands (Phase 2-3 — to build)

```
User: "Add anti-monopoly rule: no entity > 5% in my community mesh"
  → ΔT Engine rule update → Mesh sync → Confirmation required

User: "Emergency Air-Gap — disconnect from global"
  → Air-gap controller activates → local-only mode

User: "My twin should accept Python jobs up to 15 days"
  → HDT Agent Mode config → Marketplace filter set

User: "Block any ESG policy that reduces local energy sovereignty"
  → Cultural Sovereignty Layer rule added → Dharma veto pre-configured
```

### Chat Command Routing Architecture

```
User input
    ↓
Intent Classifier (AsimBrain)
    ↓
Route to:
  /api/chat       → Qwen3 LLM conversation
  /api/clones     → Clone specialist routing
  /api/jobs       → Marketplace actions
  /api/memory     → Memory operations
  /api/analytics  → System metrics
  [future] ΔT Engine, Mesh, HDT actions
    ↓
Result → Dharma check (Phase 2+)
    ↓
Response in chat
```

---

## 11. IMPLEMENTATION ROADMAP

### Phase 1 — Strong Foundation (NOW → 2 months)

```
✅ Chat + Memory working (done)
✅ 15 Clones UI — real backend (done)
✅ Dashboard — real metrics (done)
✅ Memory browser (done)
✅ Settings page — API keys (done)
✅ ASIM_NEXUS_BIBLE.md — this document (done)

✅ core/dharma/delta_t_engine.py    ← DONE (v2, PoS Simulator)
✅ core/dharma/simulate_dt.py       ← DONE (18-node simulation)
🔲 Multi-user auth proper isolation
🔲 /personal route — PersonalOS page
```

### Phase 2 — Mesh Begins + Dharma Enforced (2-6 months)

```
🔲 core/mesh/auto_discovery.py      LAN device discovery
🔲 core/mesh/p2p_node.py            2 machines talking
🔲 2-5% resource sharing            CPU/RAM offer (consent-based)
🔲 Delta Sync engine                offline-first, changes-only sync
🔲 Personal Universe container      user-scoped data isolation
🔲 Real ZKP crypto                  local key generation
🔲 Dharma rule engine               actual veto enforcement
🔲 Cultural Sovereignty Compiler    local context filter
🔲 Cognitive Firewall               narrative bias detection
```

### Phase 3 — Distributed Power (6-12 months)

```
🔲 Full Kademlia DHT mesh
🔲 ΔT Anti-monopoly live enforcement across nodes
🔲 Emergency Air-Gap protocol
🔲 Human Digital Twin full system
🔲 Agent Mode — 5/15/30-day Smart Contracts
🔲 Universe layers — Personal/Enterprise/Sovereign isolation
🔲 Community Mesh (neighborhood level)
🔲 Mobile PWA + offline sync
```

### Phase 4 — World OS (1-3 years)

```
🔲 Sovereign Mesh (org/govt level)
🔲 Global Quad Mesh
🔲 Sovereign Micro-token economy
🔲 15 specialized model routing (not just Qwen3)
🔲 Government integration APIs
🔲 Open-source public release
🔲 8 billion user architecture
```

---

## 11.5 ASIM ORB & FLOATING CHAT

### Overview
AsimOrb is the **universal floating interface** for AsimNexus — a draggable, resizable, theme-aware orb that opens a smart chat popup anywhere on screen. It connects to the real backend via WebSocket and supports voice, keyboard shortcuts, and mobile gestures.

### Files
- `frontend/react/src/components/shared/AsimOrbMaster.jsx` — Master orb component
- `frontend/react/src/components/shared/UnifiedChat.jsx` — Chat UI (compact + full mode)
- `frontend/react/src/components/shared/ComplexVisualizationOrb.jsx` — Visual effects

### Features

**Orb Behavior**
- Draggable anywhere, auto-snaps to 8 screen zones on release
- Spring-physics smoothing (60fps lerp animation)
- Position memory in `localStorage` (`asimOrbPos`)
- Glowing pulse animation, health-colored status ring
- Photo logo in circular bubble (`/ui/AsiM logo.png` fallback)

**Popup Chat**
- Draggable header bar, resizable from all 4 corners
- Min/Max size constraints (280×340 to 850×750 px)
- Size + Position memory (`asimPopupPos`, `asimPopupSize`)
- Smooth width/height transitions

**Mobile Optimization**
- Touch drag for orb and popup
- 2-finger pinch-to-resize popup
- Swipe-down on popup header to close
- Tap-hold menu (Quick Actions) for voice, themes, shortcuts
- Responsive UI: buttons, text, and padding shrink for tiny popups (<320px or <420px)

**Keyboard Shortcuts (Alt+H for help)**
| Shortcut | Action |
|----------|--------|
| Alt+Enter | Toggle Orb Open/Close |
| Alt+V | Voice Record On/Off |
| Alt+1 | Fractal Visualization |
| Alt+2 | Wave Visualization |
| Alt+3 | Spectrum (FFT) |
| Alt+Plus | Increase Popup Size |
| Alt+Minus | Decrease Popup Size |
| Alt+M | Toggle Theme (Dark → Light → Nepal → Dharma) |
| Alt+H | Show Help Menu |
| Escape | Close Popup / Cancel |

**Themes**
| Theme | Colors | Use |
|-------|--------|-----|
| Dark | Indigo/purple glow | Default |
| Light | Clean white/gray | Day use |
| Nepal | Crimson red + gold | Nepal flag inspired |
| Dharma | Saffron orange + deep blue | Sacred palette |
Theme persists in `localStorage` (`asimTheme`).

**Backend Connection**
- WebSocket to `ws://localhost:8000/ws/chat`
- Auto-connects when popup opens
- Messages sent via WebSocket first; falls back to REST `/api/brain/process`
- Connection status shown as ● (green) / ○ (gray) in chat header

**Chat Capabilities**
- Real-time messaging with AsimBrain (Qwen3-4B)
- Clone selection (Auto, Tech, Health, Finance, Legal, etc.)
- Voice input (browser SpeechRecognition, `ne-NP` locale)
- Slash commands: `/clear`, `/help`, `/clone`, `/voice`, `/search`
- Smart suggestions based on context
- File attachment support
- Screenshot analysis (native bridge)
- Responsive compose area that scales with popup size

**Visualizations in Popup Header**
- Fractal: Mandelbrot-inspired infinite zoom
- Wave: Sine wave interference patterns
- Spectrum: FFT audio visualization (active during voice recording)

### State Persistence Keys
```
localStorage:
  asimOrbPos     → {x, y}
  asimPopupPos   → {x, y}
  asimPopupSize  → {width, height}
  asimTheme      → 'dark' | 'light' | 'nepal' | 'dharma'
```

## 12. FILE STRUCTURE

```
c:\AsimNexus\
│
├── simple_backend.py              ← Main API (WORKING)
│
├── core/
│   ├── asim_brain.py              ← Unified AI routing (WORKING)
│   ├── founder_clones/
│   │   └── world_clones.py        ← 15 clone definitions (WORKING)
│   ├── economy/
│   │   └── job_marketplace.py     ← Job system (WORKING)
│   ├── dreaming/
│   │   └── dreaming_engine.py     ← Memory consolidation (WORKING)
│   └── dharma/                    ← TO BUILD (Phase 1)
│       ├── __init__.py
│       ├── delta_t_engine.py      ← ΔT math engine ← BUILDING NOW
│       ├── simulate_dt.py         ← simulation runner
│       ├── dharma_veto.py         ← veto enforcement (Phase 2)
│       └── cultural_compiler.py   ← local context (Phase 2)
│
├── connectors/
│   ├── smart_model_router.py      ← AI routing (WORKING)
│   └── unified_llm_gateway.py     ← LLM abstraction (WORKING)
│
├── mesh/                          ← TO BUILD (Phase 2)
│   ├── __init__.py
│   ├── auto_discovery.py          ← LAN device discovery
│   ├── p2p_node.py                ← peer-to-peer node
│   └── air_gap_controller.py      ← emergency isolation
│
├── docs/
│   └── ASIM_NEXUS_BIBLE.md        ← THIS FILE
│
└── frontend/react/src/
    ├── App.js                     ← Main routing (WORKING)
    ├── components/
    │   ├── UniversalChat.jsx      ← Primary interface (WORKING)
    │   ├── Dashboard.js           ← System metrics (WORKING)
    │   ├── WorldClones.jsx        ← 15 Clones (WORKING)
    │   ├── MemoryPage.jsx         ← Memory browser (WORKING)
    │   ├── SettingsPage.jsx       ← Settings (WORKING)
    │   └── shared/
    │       ├── AsimOrbMaster.jsx      ← Floating Orb (WORKING)
    │       ├── UnifiedChat.jsx        ← Chat component (WORKING)
    │       ├── ComplexVisualizationOrb.jsx  ← Visual FX (WORKING)
    │       └── AsimNexusLogo.jsx      ← Logo component (WORKING)
    └── services/
        ├── AsimBrainService.js      ← REST API client
        ├── VoiceAnalysisService.js  ← Audio recording
        ├── ContextAwarenessService.js  ← Page context
        └── GestureService.js        ← Keyboard/touch gestures
```

---

## 14. INSTALLATION & ONBOARDING (Smart Install)

### What Happens During Install?
AsimNexus installation is **not** a regular software install — it is a full **Device Intelligence Scan + Self-Configuration**.

#### Step 1: Download
Universal installer downloads for any device (Phone, Laptop, Server, IoT).

#### Step 2: Auto Hardware & Software Scan
AsimNexus scans the entire device:

| Category | What is scanned |
|----------|----------------|
| **Processor** | CPU cores, architecture, speed, threads |
| **GPU** | Graphics card, WebGL, compute capability |
| **NPU/TPU** | Neural processing units, tensor cores |
| **RAM** | Total memory, available, speed |
| **Storage** | ROM/SSD/HDD, free space, read/write speed |
| **Motherboard** | Chipset, BIOS, firmware version |
| **Sensors** | Camera, microphone, accelerometer, GPS |
| **Network** | WiFi, 5G, Bluetooth, Ethernet, Mesh-ready |
| **OS** | Current operating system, version, kernel |
| **Drivers** | Installed drivers, missing drivers |
| **Software** | Existing apps, compatibility check |
| **Security** | Vulnerabilities, permissions, firewall |
| **Environment** | Location, timezone, battery, temperature |

#### Step 3: Self-Configuration by Device Type
| Device Type | Configuration |
|-------------|---------------|
| High-end (Server/Workstation) | Full Microkernel + Complex Engine + Quantum Bridge + Wave Simulation |
| Mid-range (Laptop/Desktop) | Balanced mode — all features enabled |
| Low-end (Phone/Tablet) | Lightweight Kernel + Local-First only + Minimal UI |
| IoT/Edge | Embedded Kernel + Sensor-only mode |

#### Step 4: Core Installation
- **Dharma-Chakra Kernel** — Immutable ethical constitution
- **ΔT Engine** — Thermodynamic balance system
- **Universal Abstraction Layer** — Cross-platform compatibility
- **Floating Orb** — Asim Orb appears on screen

**Install time:** 1–5 minutes (device dependent)

---

## 15. ONBOARDING / LOGGING PROCESS (Chat-Driven)

After install, the **Floating Orb** immediately activates. The entire onboarding happens through Chat.

### Step-by-Step Flow

| Step | Action | Details |
|------|--------|---------|
| 1 | **Welcome Screen** | Language & country selection (Nepali, English, Hindi, Chinese, etc.) |
| 2 | **Device Scan** | Full hardware + environment scan (see Install section) |
| 3 | **Biometric + Identity** | Eyes, face, fingerprint + Document (Citizenship/Company/Govt ID) |
| 4 | **Role Selection** | Personal (100%) / Company (49%) / Community (Shared) / Government (51%) |
| 5 | **51%/49% Agreement** | Read & Accept Sovereign Partnership terms |
| 6 | **Policies & Permissions** | Tick: Local-First, Mesh Sharing, Dharma Bind, ZKP, Final3, Dream Learn |
| 7 | **Personal Universe** | Import documents, photos, accounts, skills, preferences |
| 8 | **Final 3 Confirmation** | 3 biometric-locked YES confirmations |
| 9 | **Activation** | Asim Orb becomes your permanent floating interface |

### After Onboarding
- **Auto-Login forever**: Biometric + ZKP (no passwords needed)
- **Asim Orb always available**: Floats on any screen, any app
- **Context-Aware**: Understands which app is open, adapts responses
- **Offline-First**: Works without internet, syncs when online

---

## 16. WHO CAN USE ASIMNEXUS & HOW?

### Individual Person (100% Personal Universe)
- **Control**: Complete ownership of your data, life, health, work
- **Via Chat**: "मेरो स्वास्थ्य रिपोर्ट देऊ", "आजको schedule बनाउ", "मेरो photo analyze गर"
- **Access**: Floating Orb anywhere + Full Dashboard

### Company (49% Partnership)
- **Control**: Enterprise Universe — HR, Finance, Production, Contracts
- **Via Chat**: "Company Mode ON", "नयाँ employee onboarding गर", "Sales report बनाउ"
- **Requirement**: Company registration + 51%/49% Agreement Accept

### Community (Shared Mesh)
- **Control**: Village/Community level resource sharing, services
- **Via Chat**: "Community Mesh join गर", "Resource sharing 3% मा सेट गर"
- **Requirement**: Community Leader Role + Agreement

### Government (51% Sovereign)
- **Control**: National Layer — Policy, Services, Security, Tax
- **Via Chat**: "Government Mode ON", "National health dashboard देऊ", "Emergency alert send गर"
- **Requirement**: Government Official ID + Sovereign Agreement

### Key Rule for ALL
- **Dharma-Chakra binds everyone** — No unethical actions possible
- **Final 3 Confirmation** — Critical actions need 3 biometric approvals
- **AI assists, Human decides** — Always

---

## 17. WHAT CAN YOU DO THROUGH CHAT?

### Personal Life Management
- "मेरो स्वास्थ्य रिपोर्ट देऊ" → Health check + recommendations
- "आजको schedule बनाउ" → Calendar + task management
- "मेरो family photo analyze गर" → AI vision analysis
- "मेरो bank balance check गर" → Financial overview

### Modify/Build AsimNexus Itself (Self-Evolving)
- "Asim Orb लाई सानो बनाउ" → UI modification
- "नयाँ फिचर थप: Voice Waveform" → Feature addition
- "Complex Visualization Module मा Wave Simulation थप" → Module creation
- "Database मा नयाँ table बनाउ" → Schema modification
- "SQL Subquery optimize गर" → Performance optimization

### Documents, Files, Photos, APIs
- "यो photo लाई मेरो Universe मा save गर" → Image storage + analysis
- "यो PDF document analyze गर र summary देऊ" → Document AI
- "Google Drive API जोड" → Third-party integration
- "यो file लाई mesh मा share गर" → P2P file sharing

### Complex Technical Tasks
- "SQL मा subquery प्रयोग गरेर top 10 customers को report बनाउ"
- "WHERE clause मा subquery राखेर dynamic filter बनाउ"
- "Complex Number प्रयोग गरेर Wave Propagation simulate गर"
- "DeltaT Engine मा नयाँ resonance detection थप"

### System Control
- "Switch to Government Mode" → Role switch
- "Agent Mode ON गर 15 दिनको लागि" → AI agent activation
- "Full Mesh Simulation चलाउ" → Network simulation
- "Dreaming Engine लाई optimize गर" → Background optimization

---

## 18. ASIMNEXUS के हो? (What is AsimNexus?)

**AsimNexus = Multiversal Autonomous Operating System (MAOS)**

It is the world's first **human-centered, decentralized, self-operating Universal OS**.

### Core Philosophy
- **Mirror World** — Digital twin of the physical world
- **Personal Universe** — Every person gets their own sovereign digital space
- **Quad-Mesh** — Personal → Community → Enterprise → Sovereign → Global
- **Machine Works, Human Decides** — AI executes, human approves

### Architecture
| Layer | Component | Purpose |
|-------|-----------|---------|
| **Kernel** | Dharma-Chakra Microkernel | Immutable ethical constitution (Hash-Locked) |
| **Engine** | ΔT (Delta-T) Engine | Thermodynamic balance: Energy + i·Entropy |
| **Intelligence** | AsimBrain (Qwen3-4B) | Local LLM with 15 Founder Clones |
| **Memory** | Vector Memory + Dreaming Engine | Background learning & consolidation |
| **Network** | Quad-System Mesh | Citizen + Corporate + Govt + Community |
| **Identity** | ZKP + Biometric | Zero-knowledge human verification |
| **Economy** | Job Marketplace + Micro-tokens | DePIN + Dharma-gated contracts |
| **Interface** | Asim Orb (Floating Chat) | Universal control from anywhere |

### Security Model
- **Local-First** — Data stays on your device
- **Dharma-Chakra** — AI cannot violate ethics (kernel-level lock)
- **Final 3 Confirmation** — 3 biometric checks for critical actions
- **Zero-Knowledge Proof** — Verify without exposing data
- **Air-Gap Mode** — Emergency offline isolation

---

## 19. HOW SOFTWARE INSTALLATION WORKS (Any Software in AsimNexus)

When you install any software inside AsimNexus:

1. **Device Scan** → Checks compatibility with your hardware (CPU, GPU, RAM, OS)
2. **Permission Request** → Asks for: File access, Network, Camera, Mic, Location
3. **Dharma Check** → Software is scanned for unethical code/malware
4. **Agreement Display** → Shows: Terms, Privacy Policy, Data usage, 51%/49% if applicable
5. **Tick Boxes** → You tick: ☑ I agree to Terms, ☑ I agree to Privacy, ☑ Dharma-aligned
6. **Accept / Reject** → You choose: Accept All, Custom (pick permissions), Reject
7. **Sandbox Install** → Software runs in isolated container first
8. **Final Confirmation** → Biometric approve for system-level software

**Your control**: You can reject any permission, uninstall anytime, and all data stays Local-First.

---

## 13. HOW TO RUN NOW

```bash
# 1. Start Backend (PowerShell)
cd c:\AsimNexus
python simple_backend.py

# 2. Start Frontend (new PowerShell tab)
cd c:\AsimNexus\frontend\react
npm start

# 3. Access
#    Chat:        http://localhost:3000
#    Dashboard:   http://localhost:3000/dashboard
#    Clones:      http://localhost:3000/clones
#    Memory:      http://localhost:3000/memory
#    Settings:    http://localhost:3000/settings
#    API Docs:    http://localhost:8000/docs
#    Health:      http://localhost:8000/health
```

### Test ΔT Engine (after building)

```bash
# Run simulation
python -m core.dharma.simulate_dt

# Expected output:
# Node A: influence=0.06, OVER CAP → attenuation applied → effective=0.048
# Node B: influence=0.04, within cap → no action
# ΔT Scores: [A:+0.02, B:-0.02] → balanced
```

---

*"जय धर्मचक्र — Machine works. Human decides. Always."*
*AsimNexus — Digital Sovereignty for 8 Billion People*
*Version 4.1 — Honest, Local-First, Math-Grounded*
