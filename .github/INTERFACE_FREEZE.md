# Interface Freeze — v1.0.1

## Frozen Interfaces
These interfaces MUST NOT change without a hotfix review:

### Mesh Protocol
- `P2PMessage` format (msg_type, sender_id, payload, timestamp, msg_id)
- PeerInfo fields (node_id, host, port_udp, port_ws)
- Bootstrap request/response message schemas
- CRDT operation format (CRDTOperation fields)
- DHT RPC message types (PING, FIND_NODE, FIND_VALUE, STORE)

### API Endpoints (all /api/* routes)
- Request/response JSON schemas
- HTTP status code conventions
- Authentication header format (Bearer JWT)
- Error response format

### Consensus Protocol
- Proposal format (proposal_id, title, description, metadata)
- Vote format (voter_id, choice, confidence, weight)
- Delegation chain format
- Arbitration result format

### OS Control Protocol
- Tool execution request/response schemas
- Sandbox configuration format
- Audit event format

## Change Process
1. Any proposed interface change must be filed as a GitHub Issue with "interface-change" label
2. Must be reviewed by 2 maintainers minimum
3. Must include migration plan for existing consumers
4. Must update API_CONTRACT_INDEX.md
5. Breaking changes trigger minor version bump (v1.1.0)
