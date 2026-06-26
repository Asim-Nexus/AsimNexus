# AsimNexus - Complete Architecture

## Root Files (3 Python, 15 Markdown)
- `app.py` - FastAPI backend entry point (184 lines)
- `asim_config.py` - Configuration manager
- `complete_system_test.py` - System integration test
- `README.md` - Project documentation
- `TECHNICAL_PROPOSAL.md` - Gov submission
- Compliance docs (VAPT, GIDC, MoCIT)

## Folders Structure

| Folder | Python | JSX | Purpose |
|--------|--------|-----|---------|
| **connectors** | 80 | 0 | 956 entities (ministries, hospitals, palikas, banks, ISPs) |
| **core** | 324 | 0 | Consensus (15 Clones), Compliance (51/49), Life Journey (6 stages) |
| **security** | 51 | 0 | ZKP, HSM, Power Balance, Zero Trust |
| **mesh** | 26 | 0 | Offline-first sync, CRDT, P2P transport |
| **economy** | 7 | 0 | Wallet, Tokens, Staking, Marketplace, Escrow |
| **database** | 2 | 0 | PostgreSQL migration |
| **docker** | 0 | 0 | Docker Compose + Dockerfiles |
| **frontend** | 4 | 55 | React 18 UI components |
| **os_control** | 30 | 0 | OS tools (47 registered) |
| **tools** | 4 | 0 | Unified tools barrel |
| **tests** | 78 | 0 | Integration tests |
| **infrastructure** | 2 | 0 | GIDC compliance |
| **compliance** | 3 | 0 | VAPT processes |
| **docs** | 0 | 0 | Documentation |
| **data** | 0 | 0 | Runtime data |

## Archived (Reference Only)
- **DigitalNepal-backend/** - Original backend (19 Python)
- **desktop_archive/** - Archived Electron
- **mobile_archive/** - Archived React Native

## To Run
```bash
# Start
uvicorn app:app --port 8000
cd frontend; npm start

# Test
python complete_system_test.py

# Docker
docker-compose -f docker/docker-compose.yml up -d
```