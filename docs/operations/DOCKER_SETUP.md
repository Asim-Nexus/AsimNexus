# AsimNexus Docker Setup & Mesh Connection Guide

This guide covers:
1. Running AsimNexus in Docker on the **primary computer**
2. Pushing to **GitHub**
3. Running AsimNexus in Docker on a **second laptop**
4. Connecting both devices via **mesh networking**

---

## Prerequisites

- **Docker Desktop** installed on both machines
- Both machines on the **same WiFi network** (or same LAN)
- **Git** installed on the primary machine
- A **GitHub account** with repository created

---

## 1. Primary Computer — Docker Setup

### 1.1 Build the Docker Image

```bash
cd C:\AsimNexus
docker compose build asimnexus
```

This builds the AsimNexus backend image using the multi-stage Dockerfile.

### 1.2 Start the Container

```bash
docker compose up -d asimnexus
```

This starts the container in detached mode with:
- **Port 8000** → Main API (REST endpoints)
- **Port 8080** → Alternative API
- **Port 7331** (UDP) → LAN Discovery
- **Port 7332** (UDP) → Kademlia DHT
- **Port 7333** → WebSocket P2P
- **Port 7334** → Relay Service
- **Port 7335** → Bootstrap Service
- **Port 7336** (UDP) → Rendezvous Service

### 1.3 Verify It's Running

```bash
# Check container status
docker ps

# Check health endpoint
curl http://localhost:8000/health

# Check OS tools
curl http://localhost:8000/api/os/tools

# Check mesh status
curl http://localhost:8000/api/mesh/discovery/status
```

### 1.4 View Logs

```bash
docker logs asimnexus-master -f
```

### 1.5 Stop the Container

```bash
docker compose down
```

---

## 2. Push to GitHub

### 2.1 Create GitHub Repository

1. Go to https://github.com
2. Click **New repository**
3. Repository name: `AsimNexus`
4. Visibility: **Public**
5. **Do NOT** initialize with README, .gitignore, or license
6. Click **Create repository**

### 2.2 Add Remote and Push

```bash
# Add the remote
git remote add origin https://github.com/AsimNexus/AsimNexus.git

# Push to GitHub
git push -u origin main
```

### 2.3 Verify on GitHub

Visit `https://github.com/AsimNexus/AsimNexus` to verify all files are pushed.

---

## 3. Second Laptop — Docker Setup

### 3.1 Install Prerequisites

On the second laptop:

1. Install **Docker Desktop** from https://www.docker.com/products/docker-desktop/
2. Install **Git** from https://git-scm.com/

### 3.2 Clone the Repository

```bash
git clone https://github.com/AsimNexus/AsimNexus.git
cd AsimNexus
```

### 3.3 Create `.env` File

```bash
# Generate a JWT secret
python -c "import secrets; print(secrets.token_hex(32))"

# Create .env file with the generated secret
```

Create `.env` with:
```env
ASIM_JWT_SECRET=<generated-secret>
ASIM_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
ASIM_DB_PATH=data/asim_core.db
ASIM_DATA_DIR=data
ASIM_LOG_LEVEL=INFO
ASIM_MESH_DISCOVERY_PORT=7331
ASIM_MESH_DISCOVERY_INTERVAL=30
ASIM_MESH_BEACON_INTERVAL=60
ASIM_MESH_DHT_PORT=7332
ASIM_MESH_P2P_PORT=7333
ASIM_MESH_RELAY_PORT=7334
ASIM_MESH_BOOTSTRAP_PORT=7335
ASIM_MESH_RENDEZVOUS_PORT=7336
ASIM_MESH_DEFAULT=local
ASIM_MESH_AUTO_RECOVER=true
ASIM_MESH_ENABLE_RELAY=true
ASIM_MESH_ENABLE_RENDEZVOUS=true
ASIM_MESH_ENABLE_MULTIHOP=true
REACT_APP_API_URL=http://localhost:8000
```

### 3.4 Build and Start

```bash
docker compose build asimnexus
docker compose up -d asimnexus
```

### 3.5 Verify

```bash
curl http://localhost:8000/health
```

---

## 4. Connect Both Devices via Mesh

### 4.1 Find IP Addresses

On **Computer 1** (primary):
```bash
ipconfig
# Look for: IPv4 Address. . . . . . . . . . . : 192.168.x.x
```

On **Laptop 2** (secondary):
```bash
ipconfig
# Look for: IPv4 Address. . . . . . . . . . . : 192.168.x.x
```

### 4.2 Connect Laptop to Computer's Bootstrap

On **Laptop 2**, add Computer 1 as a bootstrap peer:

```bash
curl -X POST http://localhost:8000/api/mesh/discover/add-peer \
  -H "Content-Type: application/json" \
  -d '{"host": "192.168.x.x", "port": 7335}'
```

Replace `192.168.x.x` with Computer 1's actual IP address.

### 4.3 Start Discovery on Both Devices

On **Computer 1**:
```bash
curl -X POST http://localhost:8000/api/mesh/discover/start
```

On **Laptop 2**:
```bash
curl -X POST http://localhost:8000/api/mesh/discover/start
```

### 4.4 Check Connected Peers

On either device:
```bash
curl http://localhost:8000/api/mesh/peers
```

Expected output shows both devices connected:
```json
{
  "peers": [
    {"id": "asim-node-...", "host": "192.168.x.x", "port": 7333, "status": "connected"},
    {"id": "asim-node-...", "host": "192.168.x.x", "port": 7333, "status": "connected"}
  ]
}
```

### 4.5 Check Mesh Discovery Status

```bash
curl http://localhost:8000/api/mesh/discovery/status
```

### 4.6 Verify Auto-Discovery (Same WiFi)

If both devices are on the same WiFi, auto-discovery should find each other automatically within 30 seconds (the discovery interval). Check with:

```bash
curl http://localhost:8000/api/mesh/discovery/status
```

Look for `"discovered_nodes"` in the response.

---

## 5. Testing the Mesh Connection

### 5.1 Test P2P Communication

Once connected, you can test P2P communication:

```bash
# On Computer 1 — check DHT status
curl http://localhost:8000/api/dht/status

# On Laptop 2 — find peers by capability
curl "http://localhost:8000/api/dht/find?capability=compute"
```

### 5.2 Test Resource Sharing

```bash
# Check resource sharing status
curl http://localhost:8000/api/personal/resource-sharing
```

### 5.3 Test Offline Sync

```bash
# Check offline sync capabilities
curl http://localhost:8000/api/mesh/offline/capabilities
```

---

## 6. Troubleshooting

### 6.1 Firewall Issues

Windows Firewall may block mesh ports. Allow them:

```powershell
# Run as Administrator
netsh advfirewall firewall add rule name="AsimNexus Mesh 7331" dir=in action=allow protocol=udp localport=7331
netsh advfirewall firewall add rule name="AsimNexus Mesh 7332" dir=in action=allow protocol=udp localport=7332
netsh advfirewall firewall add rule name="AsimNexus Mesh 7333" dir=in action=allow protocol=tcp localport=7333
netsh advfirewall firewall add rule name="AsimNexus Mesh 7334" dir=in action=allow protocol=tcp localport=7334
netsh advfirewall firewall add rule name="AsimNexus Mesh 7335" dir=in action=allow protocol=tcp localport=7335
netsh advfirewall firewall add rule name="AsimNexus Mesh 7336" dir=in action=allow protocol=udp localport=7336
```

### 6.2 Docker Network Issues

If containers can't communicate, check Docker network:

```bash
docker network inspect asimnexus-network
```

### 6.3 Container Not Starting

Check logs:
```bash
docker logs asimnexus-master
```

### 6.4 Port Conflicts

If ports 8000 or 7331-7336 are already in use, modify `docker-compose.yml` to use different host ports:

```yaml
ports:
  - "8001:8000"   # Map host 8001 → container 8000
  - "7331:7331/udp"
```

---

## 7. Architecture Overview

```
┌─────────────────────┐         ┌─────────────────────┐
│   Computer 1        │         │   Laptop 2          │
│   (Primary)         │         │   (Secondary)        │
│                     │         │                     │
│  ┌───────────────┐  │         │  ┌───────────────┐  │
│  │ Docker        │  │         │  │ Docker        │  │
│  │ Container     │  │         │  │ Container     │  │
│  │               │  │         │  │               │  │
│  │ Port 8000     │  │         │  │ Port 8000     │  │
│  │ (API)         │  │         │  │ (API)         │  │
│  │               │  │         │  │               │  │
│  │ Port 7331-36 │◄─┼─────────┼─►│ Port 7331-36  │  │
│  │ (Mesh)       │  │  WiFi   │  │ (Mesh)        │  │
│  └───────────────┘  │         │  └───────────────┘  │
│                     │         │                     │
│  IP: 192.168.x.x    │         │  IP: 192.168.x.x    │
└─────────────────────┘         └─────────────────────┘
```

### Mesh Protocol Stack

| Layer | Protocol | Port | Purpose |
|-------|----------|------|---------|
| Discovery | UDP Broadcast | 7331 | Find peers on LAN |
| DHT | UDP (Kademlia) | 7332 | Distributed hash table |
| P2P | WebSocket | 7333 | Peer-to-peer messages |
| Relay | TCP/UDP | 7334 | Relay for NAT traversal |
| Bootstrap | TCP | 7335 | Initial peer discovery |
| Rendezvous | UDP | 7336 | NAT hole punching |

---

## 8. Quick Start (TL;DR)

### On Computer 1:
```bash
cd C:\AsimNexus
docker compose build asimnexus
docker compose up -d asimnexus
```

### On GitHub:
```bash
git remote add origin https://github.com/AsimNexus/AsimNexus.git
git push -u origin main
```

### On Laptop 2:
```bash
git clone https://github.com/AsimNexus/AsimNexus.git
cd AsimNexus
# Create .env file
docker compose build asimnexus
docker compose up -d asimnexus
# Connect to Computer 1
curl -X POST http://localhost:8000/api/mesh/discover/add-peer \
  -H "Content-Type: application/json" \
  -d '{"host": "192.168.1.100", "port": 7335}'
curl -X POST http://localhost:8000/api/mesh/discover/start
```

### Verify Connection (on either):
```bash
curl http://localhost:8000/api/mesh/peers
```
