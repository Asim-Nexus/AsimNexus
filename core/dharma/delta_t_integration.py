
"""
STATUS: PARTIAL — Auto-labeled by batch_label.py
"""

"""
ASIMNEXUS ΔT Engine Integration
================================
Integrates ΔT Engine with Database and Mesh layers
Real-time influence tracking with data persistence
"""

import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio

logger = logging.getLogger("ASIM_DELTA_T_INTEGRATION")

@dataclass
class InfluenceRecord:
    """Influence tracking record"""
    id: str
    entity_id: str
    entity_type: str  # 'user', 'ai_clone', 'organization', 'node'
    influence_score: float
    delta_t_score: float
    timestamp: datetime
    action_type: str
    details: Dict[str, Any]
    veto_status: Optional[str]  # None, 'pending', 'vetoed', 'approved'

class DeltaTIntegration:
    """
    ΔT Engine Integration Layer
    
    Connects ΔT calculations with:
    - Local Database (SQLite) - personal influence tracking
    - Community Database (PostgreSQL) - shared mesh influence
    - Real-time monitoring and auto-veto
    """
    
    def __init__(self):
        self.local_db = None
        self.community_db = None
        self.delta_t_production = None
        
        # Monitoring state
        self.monitoring_active = False
        self.influence_threshold = 0.05  # 5% Gini coefficient threshold
        self.auto_veto_enabled = True
        
        # Cache for recent calculations
        self.recent_calculations: List[Dict] = []
        self.max_cache_size = 1000
        
        # Background task
        self._monitor_task = None
        
        logger.info("🔥 ΔT Integration initialized")
    
    async def initialize(self):
        """Initialize database connections"""
        logger.info("Connecting ΔT to databases...")
        
        # Connect to local database
        try:
            from core.database import get_local_db
            self.local_db = get_local_db()
            logger.info("  ✅ Local DB connected")
        except Exception as e:
            logger.error(f"  ❌ Local DB failed: {e}")
        
        # Connect to community database
        try:
            from core.database import get_community_db
            self.community_db = await get_community_db()
            logger.info("  ✅ Community DB connected")
        except Exception as e:
            logger.error(f"  ❌ Community DB failed: {e}")
        
        # Initialize ΔT production engine
        try:
            from core.dharma.delta_t_production import get_delta_t_production
            self.delta_t_production = get_delta_t_production()
            logger.info("  ✅ ΔT Production engine ready")
        except Exception as e:
            logger.error(f"  ❌ ΔT Production failed: {e}")
        
        # Create influence tracking tables
        await self._init_tables()
        
        logger.info("🎉 ΔT Integration complete")
    
    async def _init_tables(self):
        """Initialize database tables for influence tracking"""
        if self.local_db:
            # Local table for personal influence
            with self.local_db._lock:
                with self.local_db._get_connection() as conn:
                    conn.executescript('''
                        CREATE TABLE IF NOT EXISTS influence_records (
                            id TEXT PRIMARY KEY,
                            entity_id TEXT NOT NULL,
                            entity_type TEXT NOT NULL,
                            influence_score REAL NOT NULL,
                            delta_t_score REAL NOT NULL,
                            timestamp TEXT NOT NULL,
                            action_type TEXT,
                            details TEXT,
                            veto_status TEXT
                        );
                        
                        CREATE INDEX IF NOT EXISTS idx_influence_entity 
                        ON influence_records(entity_id, timestamp);
                        
                        CREATE INDEX IF NOT EXISTS idx_influence_time 
                        ON influence_records(timestamp);
                        
                        CREATE INDEX IF NOT EXISTS idx_influence_veto 
                        ON influence_records(veto_status);
                    ''')
    
    async def record_influence(self, entity_id: str, entity_type: str,
                            action_type: str, details: Dict) -> InfluenceRecord:
        """Record influence event and calculate ΔT"""
        
        # Calculate current ΔT
        delta_t_data = await self._calculate_delta_t()
        
        # Calculate influence score based on action
        influence_score = self._calculate_influence_score(entity_type, action_type, details)
        
        # Check if exceeds threshold
        exceeds_threshold = delta_t_data['gini_coefficient'] > self.influence_threshold
        
        # Determine veto status
        veto_status = None
        if exceeds_threshold and self.auto_veto_enabled:
            veto_status = 'pending'
            logger.warning(f"🚨 High influence detected: {entity_id} ({influence_score:.2%})")
        
        # Create record
        record = InfluenceRecord(
            id=f"inf_{datetime.now().strftime('%Y%m%d%H%M%S')}_{entity_id[:8]}",
            entity_id=entity_id,
            entity_type=entity_type,
            influence_score=influence_score,
            delta_t_score=delta_t_data['gini_coefficient'],
            timestamp=datetime.now(),
            action_type=action_type,
            details=details,
            veto_status=veto_status
        )
        
        # Store in local database
        if self.local_db:
            self.local_db.insert('influence_records', {
                'id': record.id,
                'entity_id': record.entity_id,
                'entity_type': record.entity_type,
                'influence_score': record.influence_score,
                'delta_t_score': record.delta_t_score,
                'timestamp': record.timestamp.isoformat(),
                'action_type': record.action_type,
                'details': json.dumps(record.details),
                'veto_status': record.veto_status
            })
        
        # Cache recent
        self.recent_calculations.append({
            'record_id': record.id,
            'entity_id': entity_id,
            'influence': influence_score,
            'delta_t': delta_t_data['gini_coefficient'],
            'timestamp': record.timestamp.isoformat(),
            'veto_status': veto_status
        })
        
        # Trim cache
        if len(self.recent_calculations) > self.max_cache_size:
            self.recent_calculations = self.recent_calculations[-self.max_cache_size:]
        
        # Trigger veto if needed
        if veto_status == 'pending':
            await self._trigger_veto(record)
        
        return record
    
    async def _calculate_delta_t(self) -> Dict[str, Any]:
        """Calculate current ΔT status"""
        if self.delta_t_production:
            return self.delta_t_production.get_delta_t_status()
        else:
            # Fallback
            return {
                'gini_coefficient': 0.0,
                'symmetry_score': 1.0,
                'timestamp': datetime.now().isoformat()
            }
    
    def _calculate_influence_score(self, entity_type: str, action_type: str, 
                                  details: Dict) -> float:
        """Calculate influence score for an action"""
        base_scores = {
            'user': 0.01,
            'ai_clone': 0.02,
            'organization': 0.05,
            'node': 0.03
        }
        
        action_multipliers = {
            'read': 0.1,
            'write': 0.3,
            'execute': 0.5,
            'admin': 1.0,
            'contract_create': 0.4,
            'contract_execute': 0.6,
            'mesh_broadcast': 0.3
        }
        
        base = base_scores.get(entity_type, 0.01)
        multiplier = action_multipliers.get(action_type, 0.2)
        
        # Adjust based on details
        if 'data_size' in details:
            size_factor = min(details['data_size'] / 1000000, 1.0)  # Cap at 1MB
            multiplier += size_factor * 0.1
        
        return min(base * multiplier, 0.1)  # Cap at 10%
    
    async def _trigger_veto(self, record: InfluenceRecord):
        """Trigger automatic veto for high influence"""
        logger.warning(f"🔴 AUTO-VETO triggered for {record.entity_id}")
        
        # Emit event to microkernel
        try:
            from core.microkernel import get_kernel_sync
            kernel = get_kernel_sync()
            if kernel:
                kernel.emit_event(
                    'dharma_veto',
                    'delta_t_integration',
                    {
                        'record_id': record.id,
                        'entity_id': record.entity_id,
                        'influence_score': record.influence_score,
                        'delta_t_score': record.delta_t_score,
                        'reason': 'High influence detected',
                        'auto': True
                    },
                    priority=9  # High priority
                )
        except Exception as e:
            logger.error(f"Failed to emit veto event: {e}")
        
        # Update record status
        if self.local_db:
            self.local_db.update('influence_records', record.id, {
                'veto_status': 'vetoed',
                'details': json.dumps({
                    **record.details,
                    'veto_reason': 'Auto-veto: Influence threshold exceeded',
                    'veto_timestamp': datetime.now().isoformat()
                })
            })
    
    async def manual_veto(self, record_id: str, reason: str, user_id: str) -> bool:
        """Manual veto by human user"""
        if not self.local_db:
            return False
        
        record = self.local_db.get('influence_records', record_id)
        if not record:
            return False
        
        # Update status
        self.local_db.update('influence_records', record_id, {
            'veto_status': 'vetoed',
            'details': json.dumps({
                **json.loads(record.get('details', '{}')),
                'manual_veto': True,
                'veto_reason': reason,
                'veto_by': user_id,
                'veto_timestamp': datetime.now().isoformat()
            })
        })
        
        logger.info(f"✅ Manual veto applied: {record_id} by {user_id}")
        return True
    
    async def get_influence_history(self, entity_id: str = None, 
                                  since: datetime = None,
                                  limit: int = 100) -> List[InfluenceRecord]:
        """Get influence history from database"""
        if not self.local_db:
            return []
        
        # Build query
        where_clause = "1=1"
        params = []
        
        if entity_id:
            where_clause += " AND entity_id = ?"
            params.append(entity_id)
        
        if since:
            where_clause += " AND timestamp > ?"
            params.append(since.isoformat())
        
        # Query database
        with self.local_db._lock:
            with self.local_db._get_connection() as conn:
                conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
                cursor = conn.execute(
                    f"SELECT * FROM influence_records WHERE {where_clause} ORDER BY timestamp DESC LIMIT ?",
                    params + [limit]
                )
                rows = cursor.fetchall()
        
        # Convert to records
        records = []
        for row in rows:
            records.append(InfluenceRecord(
                id=row['id'],
                entity_id=row['entity_id'],
                entity_type=row['entity_type'],
                influence_score=row['influence_score'],
                delta_t_score=row['delta_t_score'],
                timestamp=datetime.fromisoformat(row['timestamp']),
                action_type=row['action_type'],
                details=json.loads(row['details']) if row['details'] else {},
                veto_status=row['veto_status']
            ))
        
        return records
    
    async def get_current_status(self) -> Dict[str, Any]:
        """Get current ΔT integration status"""
        delta_t = await self._calculate_delta_t()
        
        # Get recent high influence events
        recent_high = [
            calc for calc in self.recent_calculations
            if calc.get('veto_status') == 'pending'
        ]
        
        # Get stats from database
        stats = {'total_records': 0, 'vetoed': 0, 'pending': 0}
        if self.local_db:
            with self.local_db._lock:
                with self.local_db._get_connection() as conn:
                    stats['total_records'] = conn.execute(
                        "SELECT COUNT(*) FROM influence_records"
                    ).fetchone()[0]
                    stats['vetoed'] = conn.execute(
                        "SELECT COUNT(*) FROM influence_records WHERE veto_status = 'vetoed'"
                    ).fetchone()[0]
                    stats['pending'] = conn.execute(
                        "SELECT COUNT(*) FROM influence_records WHERE veto_status = 'pending'"
                    ).fetchone()[0]
        
        return {
            'delta_t': delta_t,
            'monitoring_active': self.monitoring_active,
            'auto_veto_enabled': self.auto_veto_enabled,
            'threshold': self.influence_threshold,
            'recent_high_influence_events': len(recent_high),
            'database_stats': stats,
            'cache_size': len(self.recent_calculations)
        }
    
    async def start_monitoring(self, interval_seconds: int = 30):
        """Start real-time monitoring"""
        self.monitoring_active = True
        self._monitor_task = asyncio.create_task(
            self._monitoring_loop(interval_seconds)
        )
        logger.info(f"🔍 Real-time monitoring started ({interval_seconds}s interval)")
    
    async def _monitoring_loop(self, interval: int):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                # Calculate current ΔT
                status = await self.get_current_status()
                
                # Check threshold
                if status['delta_t']['gini_coefficient'] > self.influence_threshold:
                    logger.warning(
                        f"🚨 ΔT Alert: Gini = {status['delta_t']['gini_coefficient']:.2%}"
                    )
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(interval)
    
    async def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.monitoring_active = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("🔍 Monitoring stopped")

_delta_t_integration = None

async def get_delta_t_integration() -> DeltaTIntegration:
    """Get ΔT integration singleton"""
    global _delta_t_integration
    if _delta_t_integration is None:
        _delta_t_integration = DeltaTIntegration()
        await _delta_t_integration.initialize()
    return _delta_t_integration

if __name__ == "__main__":
    import asyncio
    import sys
    
    async def main():
        integration = await get_delta_t_integration()
        
        if len(sys.argv) > 1 and sys.argv[1] == "test":
            # Test recording
            record = await integration.record_influence(
                "test_user_001",
                "user",
                "contract_create",
                {"contract_value": 1000}
            )
            print(f"Recorded: {record.id}")
            print(f"Influence: {record.influence_score:.2%}")
            print(f"ΔT: {record.delta_t_score:.2%}")
            print(f"Veto: {record.veto_status}")
            
        elif len(sys.argv) > 1 and sys.argv[1] == "status":
            print(json.dumps(await integration.get_current_status(), indent=2))
        
        else:
            print("Usage: python delta_t_integration.py [test|status]")
    
    asyncio.run(main())
