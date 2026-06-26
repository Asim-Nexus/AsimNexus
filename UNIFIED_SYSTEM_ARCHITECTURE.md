# AsimNexus - Unified System Architecture
# All Layers Connected & Integrated

## Folder Structure (Final Merged)

```
AsimNexus/
├── app.py                          # FastAPI backend (entry point)
├── asim_config.py                  # Configuration
├── complete_system_test.py           # Full system test
├── test_full_integration.py          # Integration test
├── start_asimnexus.py              # Auto-start script
├── ARCHITECTURE.md                 # This file
├── CONNECTORS.md                   # Entity docs
├── DOCKER_READY.md                 # Docker setup
├── GOVERNMENT_COMPLIANCE_PLAN.md   # Nepal Gov compliance
├── GO_LIVE_ROADMAP.md              # Go-live timeline
├── FINAL_MERGE_REPORT.md           # Merge status
├── TECHNICAL_PROPOSAL.md           # Gov submission
├── README.md                       # Project readme
│
├── connectors/                     # ALL ENTITIES (956)
│   ├── __init__.py                 # Unified exports
│   ├── nepal/government.py         # 18 ministries, 77 districts, 30 banks, 20 ISPs, 12 universities, 7 schools
│   ├── health/hospitals.py         # 12 hospitals
│   ├── local/palikas.py            # 753 palikas
│   └── tourism/hotels.py           # 20 hotels
│
├── core/                           # CORE ENGINES (324 files)
│   ├── consensus_engine.py         # 15 Founder Clones
│   ├── compliance_engine.py        # 51/49 Power Balance
│   ├── life_journey.py             # 6 Life Stages
│   ├── entity_bridge.py            # Integration
│   ├── gov_standards.py            # Gov compliance API
│   └── [20+ subdirectories with full engine]
│
├── security/                       # SECURITY LAYER (51 files)
│   ├── __init__.py                 # ZKP + HSM exports
│   ├── zkp_privacy.py              # Zero-Knowledge Proof
│   ├── hsm_integration.py          # Hardware Security Module
│   ├── power_balance_constitution.py # Constitution
│   └── zero_trust.py               # Zero Trust Security
│
├── mesh/                           # OFFLINE SYNC (26 files)
│   ├── __init__.py                 # CRDT exports
│   ├── offline_sync_engine.py      # Queue-based sync
│   ├── crdt_sync.py                # Conflict-free replication
│   ├── mesh_node.py                # P2P node
│   ├── p2p_transport.py          # WebSocket transport
│   └── kademlia_dht.py             # Distributed hash table
│
├── economy/                          # ECONOMY SYSTEM (7 files)
│   ├── __init__.py                 # All economy exports
│   ├── wallet.py                   # Wallet engine
│   ├── tokens.py                   # Token registry
│   ├── escrow.py                   # Escrow engine
│   ├── marketplace.py              # Marketplace engine
│   └── staking.py                  # Staking engine
│
├── os_control/                     # OS CONTROL TOOLS (30 files)
│   ├── __init__.py                 # All tools exports
│   ├── tool_registry.py            # 47 tools registered
│   ├── capability_matrix.py        # Permissions
│   ├── os_tool_executor.py         # Tool executor
│   └── openclaw_like_tools/        # OS tools implementation
│       ├── file_tools.py           # File operations
│       ├── process_tools.py        # Process tools
│       ├── system_monitor.py       # System monitoring
│       ├── clipboard_tools.py      # Clipboard ops
│       └── notification_tools.py     # Notifications
│
├── tools/                          # TOOLS BARREL (4 files)
│   ├── all_tools.py                # Unified tool list
│   ├── batch_label.py              # Labeling tool
│   └── check_import.py, check_status_labels.py
│
├── database/                       # DATABASE (2 files)
│   ├── __init__.py                 # PostgreSQL migration
│   └── migrations/postgresql.py      # SQLite to PG
│
├── docker/                         # DOCKER (configs)
│   ├── docker-compose.yml          # Full stack (5 services)
│   ├── Dockerfile.backend          # Backend image
│   └── Dockerfile.frontend         # Frontend image
│
├── frontend/                       # REACT 18 (52 components)
│   └── src/components/             # All components
│
├── tests/                          # TESTS (78 files)
│   ├── unified_test.py             # Integration test
│   └── complete_test.py, test_all_systems.py
│
├── infrastructure/                 # GIDC COMPLIANCE
│   └── gcloud_compliance.py        # GIDC setup
│
└── compliance/                     # VAPT PROCESSES
    ├── vapt_process.py             # Security audit
    └── accessibility_compliance.py   # WCAG compliance
```

## How to Run

### Development
```bash
# Start backend
uvicorn app:app --port 8000

# Start frontend
cd frontend; npm start

# Run tests
python complete_system_test.py
```

### Production (Docker)
```bash
docker-compose -f docker/docker-compose.yml up -d
```

## All Systems Tested ✅
- connectors: 956 entities
- core: 15 Founder Clones + Compliance
- security: ZKP + HSM
- mesh: OfflineSync + CRDT
- economy: 5 engines
- tools: 47 OS tools