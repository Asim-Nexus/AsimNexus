
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS ΔT Engine Mesh Integration
=====================================
ΔT Engine connected to Mesh Network
Distributed influence tracking across nodes
"""

import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import asyncio

logger = logging.getLogger("ASIM_DELTA_T_MESH")

@dataclass
class MeshInfluenceReport:
    """Influence report from mesh node"""
    node_id: str
    timestamp: datetime
    local_gini: float
    global_gini: Optional[float]
    top_influencers: List[Dict]
    veto_events: List[Dict]
    mesh_layer: str  # 'lan', 'community', 'global'

class DeltaTMeshIntegration:
    """
    ΔT Engine Mesh Integration
    
    Features:
    - Share influence data across mesh
    - Aggregate global ΔT calculations
    - Distributed veto consensus
    - Mesh-wide fairness monitoring
    """
    
    def __init__(self):
        self.mesh = None
        self.delta_t_integration = None
        
        # Mesh influence data
        self.node_reports: Dict[str, MeshInfluenceReport] = {}
        self.global_aggregation: Dict[str, Any] = {}
        
        # Consensus tracking
        self.veto_consensus: Dict[str, Dict] = {}  # veto_id -> node_votes
        
        # Sync settings
        self.sync_interval = 60  # seconds
        self.min_consensus_nodes = 3
        
        logger.info("🌐 ΔT Mesh Integration initialized")
    
    async def initialize(self):
        """Initialize mesh connection"""
        logger.info("Connecting ΔT to Mesh...")
        
        # Connect to mesh
        try:
            from core.mesh.unified_mesh import get_mesh_coordinator
            self.mesh = await get_mesh_coordinator()
            logger.info("  ✅ Mesh connected")
        except Exception as e:
            logger.error(f"  ❌ Mesh connection failed: {e}")
            return False
        
        # Connect to ΔT integration
        try:
            from core.dharma.delta_t_integration import get_delta_t_integration
            self.delta_t_integration = await get_delta_t_integration()
            logger.info("  ✅ ΔT Integration connected")
        except Exception as e:
            logger.error(f"  ❌ ΔT Integration failed: {e}")
            return False
        
        # Register message handlers
        self._register_handlers()
        
        # Start sync
        asyncio.create_task(self._sync_loop())
        
        logger.info("🎉 ΔT Mesh Integration complete")
        return True
    
    def _register_handlers(self):
        """Register mesh message handlers"""
        if not self.mesh:
            return
        
        # Handle influence reports from other nodes
        self.mesh.on('delta_t_report', self._handle_influence_report)
        
        # Handle veto proposals
        self.mesh.on('veto_proposal', self._handle_veto_proposal)
        
        # Handle veto votes
        self.mesh.on('veto_vote', self._handle_veto_vote)
        
        logger.info("  ✅ Mesh handlers registered")
    
    async def _handle_influence_report(self, data: Dict):
        """Handle influence report from another node"""
        node_id = data.get('node_id')
        if not node_id:
            return
        
        # Store report
        self.node_reports[node_id] = MeshInfluenceReport(
            node_id=node_id,
            timestamp=datetime.fromisoformat(data.get('timestamp')),
            local_gini=data.get('local_gini', 0.0),
            global_gini=data.get('global_gini'),
            top_influencers=data.get('top_influencers', []),
            veto_events=data.get('veto_events', []),
            mesh_layer=data.get('mesh_layer', 'unknown')
        )
        
        logger.debug(f"Received influence report from {node_id[:16]}")
        
        # Update global aggregation
        await self._update_global_aggregation()
    
    async def _handle_veto_proposal(self, data: Dict):
        """Handle veto proposal from another node"""
        veto_id = data.get('veto_id')
        if not veto_id:
            return
        
        # Initialize consensus tracking
        if veto_id not in self.veto_consensus:
            self.veto_consensus[veto_id] = {
                'proposal': data,
                'votes': {},
                'timestamp': datetime.now()
            }
        
        # If auto-veto is enabled locally, vote
        if self.delta_t_integration and self.delta_t_integration.auto_veto_enabled:
            await self._vote_on_veto(veto_id, True, "auto_veto")
        
        logger.info(f"Veto proposal received: {veto_id[:16]}")
    
    async def _handle_veto_vote(self, data: Dict):
        """Handle veto vote from another node"""
        veto_id = data.get('veto_id')
        node_id = data.get('node_id')
        vote = data.get('vote')  # True/False
        
        if veto_id in self.veto_consensus:
            self.veto_consensus[veto_id]['votes'][node_id] = {
                'vote': vote,
                'reason': data.get('reason'),
                'timestamp': datetime.now()
            }
            
            # Check if consensus reached
            await self._check_veto_consensus(veto_id)
    
    async def _vote_on_veto(self, veto_id: str, approve: bool, reason: str):
        """Vote on a veto proposal"""
        if not self.mesh:
            return
        
        vote_msg = {
            'type': 'veto_vote',
            'veto_id': veto_id,
            'node_id': self.mesh.node_id,
            'vote': approve,
            'reason': reason,
            'timestamp': datetime.now().isoformat()
        }
        
        # Broadcast to mesh
        await self.mesh.broadcast(vote_msg)
        
        logger.info(f"Voted {'YES' if approve else 'NO'} on {veto_id[:16]}")
    
    async def _check_veto_consensus(self, veto_id: str):
        """Check if veto has reached consensus"""
        consensus = self.veto_consensus.get(veto_id)
        if not consensus:
            return
        
        votes = consensus['votes']
        total_votes = len(votes)
        yes_votes = sum(1 for v in votes.values() if v['vote'])
        
        # Require 2/3 majority
        if total_votes >= self.min_consensus_nodes:
            if yes_votes / total_votes >= 0.67:
                # Consensus reached - execute veto
                logger.warning(f"🚨 VETO CONSENSUS reached: {veto_id[:16]}")
                await self._execute_mesh_veto(veto_id, consensus['proposal'])
    
    async def _execute_mesh_veto(self, veto_id: str, proposal: Dict):
        """Execute veto across mesh"""
        entity_id = proposal.get('entity_id')
        
        if self.delta_t_integration:
            # Record veto locally
            await self.delta_t_integration.manual_veto(
                f"mesh_{veto_id}",
                f"Mesh consensus veto: {proposal.get('reason')}",
                "mesh_consensus"
            )
        
        # Notify local systems
        try:
            from core.microkernel import get_kernel_sync
            kernel = get_kernel_sync()
            if kernel:
                kernel.emit_event(
                    'mesh_veto_executed',
                    'delta_t_mesh',
                    {
                        'veto_id': veto_id,
                        'entity_id': entity_id,
                        'consensus_nodes': len(self.veto_consensus[veto_id]['votes'])
                    },
                    priority=10
                )
        except Exception as e:
            logger.error(f"Failed to emit mesh veto event: {e}")
    
    async def _sync_loop(self):
        """Periodic sync with mesh"""
        while True:
            try:
                await self._broadcast_influence_report()
                await asyncio.sleep(self.sync_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Sync loop error: {e}")
                await asyncio.sleep(self.sync_interval)
    
    async def _broadcast_influence_report(self):
        """Broadcast local influence to mesh"""
        if not self.mesh or not self.delta_t_integration:
            return
        
        # Get local status
        status = await self.delta_t_integration.get_current_status()
        
        # Get recent high influence events
        recent_high = [
            calc for calc in self.delta_t_integration.recent_calculations[-10:]
            if calc.get('veto_status') == 'pending'
        ]
        
        report = {
            'type': 'delta_t_report',
            'node_id': self.mesh.node_id,
            'timestamp': datetime.now().isoformat(),
            'local_gini': status['delta_t']['gini_coefficient'],
            'global_gini': self.global_aggregation.get('global_gini'),
            'top_influencers': self._get_top_influencers(),
            'veto_events': recent_high,
            'mesh_layer': 'community'  # This would be determined by actual network
        }
        
        # Broadcast to mesh
        await self.mesh.broadcast(report)
        
        logger.debug(f"Broadcast influence report: Gini={report['local_gini']:.2%}")
    
    def _get_top_influencers(self, limit: int = 5) -> List[Dict]:
        """Get top influencers from recent calculations"""
        if not self.delta_t_integration:
            return []
        
        # Aggregate by entity
        entity_influence: Dict[str, float] = {}
        for calc in self.delta_t_integration.recent_calculations[-100:]:
            entity_id = calc.get('entity_id')
            if entity_id:
                entity_influence[entity_id] = entity_influence.get(entity_id, 0) + calc.get('influence', 0)
        
        # Sort and return top
        sorted_entities = sorted(
            entity_influence.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {'entity_id': eid, 'total_influence': inf}
            for eid, inf in sorted_entities[:limit]
        ]
    
    async def _update_global_aggregation(self):
        """Update global ΔT from all node reports"""
        if not self.node_reports:
            return
        
        # Aggregate local Gini coefficients
        ginis = [r.local_gini for r in self.node_reports.values()]
        if ginis:
            self.global_aggregation = {
                'global_gini': sum(ginis) / len(ginis),
                'max_gini': max(ginis),
                'min_gini': min(ginis),
                'nodes_reporting': len(ginis),
                'last_update': datetime.now().isoformat()
            }
    
    async def propose_veto(self, entity_id: str, reason: str, evidence: Dict) -> str:
        """Propose mesh-wide veto"""
        if not self.mesh:
            return None
        
        veto_id = f"veto_{datetime.now().strftime('%Y%m%d%H%M%S')}_{entity_id[:8]}"
        
        proposal = {
            'type': 'veto_proposal',
            'veto_id': veto_id,
            'entity_id': entity_id,
            'reason': reason,
            'evidence': evidence,
            'proposer': self.mesh.node_id,
            'timestamp': datetime.now().isoformat()
        }
        
        # Initialize consensus
        self.veto_consensus[veto_id] = {
            'proposal': proposal,
            'votes': {},
            'timestamp': datetime.now()
        }
        
        # Broadcast proposal
        await self.mesh.broadcast(proposal)
        
        logger.info(f"Veto proposed: {veto_id[:16]} for {entity_id[:16]}")
        return veto_id
    
    def get_mesh_status(self) -> Dict[str, Any]:
        """Get mesh-wide ΔT status"""
        return {
            'connected': self.mesh is not None,
            'nodes_reporting': len(self.node_reports),
            'global_aggregation': self.global_aggregation,
            'active_veto_proposals': len(self.veto_consensus),
            'recent_reports': [
                {
                    'node_id': r.node_id[:16] + "...",
                    'gini': r.local_gini,
                    'layer': r.mesh_layer,
                    'age_seconds': (datetime.now() - r.timestamp).seconds
                }
                for r in list(self.node_reports.values())[-5:]
            ]
        }

_delta_t_mesh = None

async def get_delta_t_mesh() -> DeltaTMeshIntegration:
    """Get ΔT mesh integration singleton"""
    global _delta_t_mesh
    if _delta_t_mesh is None:
        _delta_t_mesh = DeltaTMeshIntegration()
        await _delta_t_mesh.initialize()
    return _delta_t_mesh

if __name__ == "__main__":
    import asyncio
    import sys
    
    async def main():
        integration = await get_delta_t_mesh()
        
        if len(sys.argv) > 1 and sys.argv[1] == "status":
            print(json.dumps(integration.get_mesh_status(), indent=2))
        
        elif len(sys.argv) > 1 and sys.argv[1] == "propose":
            entity_id = sys.argv[2] if len(sys.argv) > 2 else "test_entity"
            veto_id = await integration.propose_veto(
                entity_id,
                "Test veto proposal",
                {"test": True}
            )
            print(f"Proposed veto: {veto_id}")
        
        else:
            print("Usage: python delta_t_mesh.py [status|propose <entity_id>]")
    
    asyncio.run(main())
