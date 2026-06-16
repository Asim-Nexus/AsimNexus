# File Execution Plan
## Tripartite Governance Implementation

**Generated:** 2026-06-15  
**Purpose:** Production-ready implementation checklist

---

## Phase 1: Core Governance Completion

### File 1: core/consensus/clone_consensus_voting.py
**Status:** CREATE  
**Dependencies:** core/founder_clones/founder_clone_system.py  
**Lines:** ~200

```python
"""
Clone Consensus Voting Engine
Implements 8/15 approval threshold for Constitutional AI Council
"""

import asyncio
import time
from typing import Dict, List, Optional
from enum import Enum
from dataclasses import dataclass

class VoteChoice(str, Enum):
    APPROVE = "approve"
    REJECT = "reject"
    ABSTAIN = "abstain"
    DEFER = "defer"

@dataclass
class CloneVote:
    voter_id: str
    voter_role: str
    choice: VoteChoice
    rationale: str
    timestamp: float

@dataclass  
class ConsensusRound:
    round_id: str
    proposal: str
    sector: str
    votes: List[CloneVote]
    outcome: str
    human_override: bool = False

class CloneConsensusVoting:
    """15-Member Constitutional AI Council voting mechanism."""
    
    QUORUM_THRESHOLD = 0.51  # 8/15 minimum
    
    def __init__(self, founder_system=None):
        self.founder_system = founder_system
        self._rounds: Dict[str, ConsensusRound] = {}
        
    async def start_round(
        self,
        topic: str,
        sector: str,
        description: str = ""
    ) -> ConsensusRound:
        """Execute consensus round with all 15 founders."""
        # 1. Send topic to all relevant founders
        # 2. Collect votes
        # 3. Calculate consensus
        # 4. Return result
        pass
        
    async def collect_votes(
        self,
        topic: str,
        sector: str
    ) -> List[CloneVote]:
        """Collect votes from Founder Clones."""
        pass
        
    def calculate_outcome(self, votes: List[CloneVote]) -> str:
        """Determine approval outcome (8/15 rule)."""
        approve_count = sum(1 for v in votes if v.choice == VoteChoice.APPROVE)
        if approve_count >= 8:
            return "approved"
        return "rejected"
```

### File 2: connectors/nexus_secure_connector.py
**Status:** CREATE  
**Dependencies:** security/power_balance_constitution.py, core/dharma/veto_engine.py

```python
"""
Nexus Secure Connector API
Cross-module authentication and routing with ZKP
"""

import hashlib
import secrets
from typing import Dict, Any, Optional
from enum import Enum

class ModuleType(str, Enum):
    GOVERNMENT = "government"
    ENTERPRISE = "enterprise" 
    CITIZEN = "citizen"

class NexusSecureConnector:
    """Secure API gateway for tripartite interaction."""
    
    def __init__(self):
        self.power_balance = None  # Lazy load
        self.veto_engine = None
        
    async def validate_request(
        self,
        source_module: ModuleType,
        target_module: ModuleType,
        action: str,
        context: Dict[str, Any]
    ) -> bool:
        """Validate cross-module request against sector rules."""
        # Check power balance requirements
        # Run VETO engine
        # Return validation result
        pass
        
    async def route_request(
        self,
        target_module: ModuleType,
        payload: Dict[str, Any],
        requires_human: bool = False
    ) -> Dict[str, Any]:
        """Route validated request to target module."""
        pass
```

---

## Phase 2: Component Extensions

### File 3: core/identity/digital_twin.py
**Status:** CREATE  
**Dependencies:** core/identity/user_identity.py

```python
"""
Human Digital Twin (HDT)
Citizen's personal AI agent with offline capability
"""

import uuid
from pathlib import Path
from typing import Dict, Any, Optional

class HumanDigitalTwin:
    """Nepalese citizen's digital twin with mesh networking."""
    
    def __init__(self, citizen_id: str, nid_number: str):
        self.citizen_id = citizen_id
        self.nid_number = nid_number
        self.did = f"did:asim:{citizen_id}"
        self.offline_queue = []
        self.mesh_capability = True
        
    async def execute_offline_task(self, task: str) -> Dict:
        """Queue task for offline execution."""
        self.offline_queue.append({
            "id": str(uuid.uuid4()),
            "task": task,
            "queued_at": time.time()
        })
        
    async def sync_when_online(self):
        """Sync queued operations when mesh network available."""
        pass
```

### File 4: security/hsm_integration.py
**Status:** CREATE  
**Dependencies:** External HSM library required

```python
"""
HSM Integration for Government Keys
Thales/CryptoMB hardware security module integration
"""

class HSMIntegration:
    """Hardware Security Module integration for production."""
    
    def __init__(self, hsm_config: Dict):
        self.hsm_config = hsm_config
        
    def encrypt_sensitive(self, data: bytes) -> bytes:
        """Encrypt with HSM-backed key."""
        pass
        
    def decrypt_sensitive(self, data: bytes) -> bytes:
        """Decrypt with HSM key."""
        pass
        
    def sign_level3_approval(self, payload: str) -> str:
        """Sign Level-3 approval with HSM token."""
        pass
```

---

## Phase 3: Modifications Required

### File 5: core/founder_clones/founder_clone_system.py
**Status:** MODIFY  
**Modify Lines:** 439-579

```python
# ADD after line 534 in coordinate_founders():
async def _run_consensus_voting(
    self,
    task: str,
    sector: str,
    description: str
) -> Dict:
    """Run 8/15 consensus voting if required."""
    from core.consensus.clone_consensus_voting import CloneConsensusVoting
    
    voting = CloneConsensusVoting(founder_system=self)
    result = await voting.start_round(
        topic=task,
        sector=sector,
        description=description
    )
    return result.to_dict()

# ADD after line 677:
async def clone_consensus_voting(
    self,
    proposal: str,
    sector: str = "general"
) -> Dict[str, Any]:
    """Public API for consensus voting."""
    return await self._run_consensus_voting(
        task=proposal,
        sector=sector,
        description=f"Governance vote: {proposal[:100]}"
    )
```

### File 6: core/identity/personal_os.py
**Status:** MODIFY  
**Add Lines:** ~200

```python
# ADD after line 677:
class GovernmentMode(PersonalOS):
    """Government official's Personal OS with Level-3 access."""
    
    def __init__(self, user_id: str):
        super().__init__(user_id)
        self.sector = "government"
        self.requires_level3 = True
        self.gov_permissions = ["policy_edit", "audit_access", "kill_switch"]

class EnterpriseMode(PersonalOS):
    """Enterprise employee's Personal OS."""
    
    def __init__(self, user_id: str):
        super().__init__(user_id)
        self.sector = "enterprise"
        self.data_limit_gb = 10
```

### File 7: mesh/offline_sync_engine.py
**Status:** MODIFY  
**Add Lines:** ~150

```python
# ADD after line 743:
async def queue_for_mesh(self, operation: Dict) -> str:
    """Queue operation for mesh network sync."""
    op_id = str(uuid.uuid4())
    self._pending_queue[op_id] = {
        "operation": operation,
        "timestamp": time.time(),
        "retry_count": 0
    }
    return op_id

async def sms_fallback(self, msg: str, phone: str) -> bool:
    """Nepal-specific SMS fallback for remote areas."""
    # Integrate with Nepali SMS gateway (NTC/Ncell)
    pass
```

---

## Phase 4: Testing Requirements

### Test Files to Create

| Test File | Purpose | Lines |
|-----------|---------|-------|
| `tests/real/test_clone_consensus.py` | Consensus voting tests | ~150 |
| `tests/real/test_nexus_connector.py` | Cross-module auth tests | ~100 |
| `tests/real/test_digital_twin.py` | Citizen twin tests | ~100 |
| `tests/real/test_hsm_integration.py` | HSM encryption tests | ~80 |

---

## Execution Order

```
Week 1: core/consensus/clone_consensus_voting.py
Week 2: connectors/nexus_secure_connector.py  
Week 3: core/identity/digital_twin.py
Week 4: security/hsm_integration.py
Week 5: MODIFY founder_clone_system.py
Week 6: MODIFY personal_os.py
Week 7: MODIFY offline_sync_engine.py
Week 8: All integration tests
```