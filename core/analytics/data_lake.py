"""
STATUS: REAL — OLAP Analytics & CQRS Data Lake for AsimNexus
ASIMNEXUS Data Lake
====================
CQRS (Command Query Responsibility Segregation) implementation:
- Write path: VectorMemory (core/vectormemory.py) — handles all writes
- Read/OLAP path: DataLake (this module) — handles all reads/analytics

Reference: Digital Twin Architecture (Graeme Wright),
           CQRS Pattern (Martin Fowler),
           OLAP Cube Design (Ralph Kimball)

Features:
  - OLAP-style analytics over VectorMemory snapshots
  - Materialized views for common queries
  - Time-series aggregation (hourly, daily, weekly, monthly)
  - Read-optimized query interface (CQRS read side)
  - Integration with Mirror Module for self-evolution
  - Export to structured formats for fine-tuning
  - Snapshot-based consistency (eventual consistency with VectorMemory)
"""

import json
import logging
import time
import uuid
import threading
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Callable

logger = logging.getLogger("AsimNexus.Analytics.DataLake")

DATA_LAKE_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "data_lake"
DATA_LAKE_PATH.mkdir(parents=True, exist_ok=True)

SNAPSHOTS_PATH = DATA_LAKE_PATH / "snapshots"
SNAPSHOTS_PATH.mkdir(exist_ok=True)

VIEWS_PATH = DATA_LAKE_PATH / "views"
VIEWS_PATH.mkdir(exist_ok=True)

AGGREGATIONS_PATH = DATA_LAKE_PATH / "aggregations"
AGGREGATIONS_PATH.mkdir(exist_ok=True)


class AggregationGranularity(str, Enum):
    """Time granularity for aggregations."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class SnapshotType(str, Enum):
    """Types of snapshots the Data Lake can capture."""
    MEMORY_FULL = "memory_full"
    MEMORY_DIFF = "memory_diff"
    ECONOMY_STATE = "economy_state"
    CONSENSUS_STATE = "consensus_state"
    MESH_STATE = "mesh_state"
    MIRROR_STATE = "mirror_state"
    SYSTEM_METRICS = "system_metrics"


@dataclass
class DataLakeSnapshot:
    """A point-in-time snapshot of system state."""
    snapshot_id: str
    snapshot_type: SnapshotType
    timestamp: float = field(default_factory=time.time)
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    parent_snapshot_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "snapshot_type": self.snapshot_type.value,
            "timestamp": self.timestamp,
            "data": self.data,
            "metadata": self.metadata,
            "parent_snapshot_id": self.parent_snapshot_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataLakeSnapshot":
        return cls(
            snapshot_id=data["snapshot_id"],
            snapshot_type=SnapshotType(data["snapshot_type"]),
            timestamp=data.get("timestamp", time.time()),
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
            parent_snapshot_id=data.get("parent_snapshot_id"),
        )


@dataclass
class MaterializedView:
    """A pre-computed view for fast read queries."""
    view_id: str
    view_name: str
    created_at: float = field(default_factory=time.time)
    last_refreshed: float = field(default_factory=time.time)
    data: Dict[str, Any] = field(default_factory=dict)
    query_definition: Dict[str, Any] = field(default_factory=dict)
    row_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "view_id": self.view_id,
            "view_name": self.view_name,
            "created_at": self.created_at,
            "last_refreshed": self.last_refreshed,
            "data": self.data,
            "query_definition": self.query_definition,
            "row_count": self.row_count,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MaterializedView":
        return cls(
            view_id=data["view_id"],
            view_name=data["view_name"],
            created_at=data.get("created_at", time.time()),
            last_refreshed=data.get("last_refreshed", time.time()),
            data=data.get("data", {}),
            query_definition=data.get("query_definition", {}),
            row_count=data.get("row_count", 0),
        )


@dataclass
class TimeSeriesAggregation:
    """Pre-computed time-series aggregation."""
    aggregation_id: str
    metric_name: str
    granularity: AggregationGranularity
    time_bucket: str  # ISO format date/time for the bucket
    value: float = 0.0
    count: int = 0
    min_value: float = 0.0
    max_value: float = 0.0
    sum_value: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "aggregation_id": self.aggregation_id,
            "metric_name": self.metric_name,
            "granularity": self.granularity.value,
            "time_bucket": self.time_bucket,
            "value": self.value,
            "count": self.count,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "sum_value": self.sum_value,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimeSeriesAggregation":
        return cls(
            aggregation_id=data["aggregation_id"],
            metric_name=data["metric_name"],
            granularity=AggregationGranularity(data["granularity"]),
            time_bucket=data["time_bucket"],
            value=data.get("value", 0.0),
            count=data.get("count", 0),
            min_value=data.get("min_value", 0.0),
            max_value=data.get("max_value", 0.0),
            sum_value=data.get("sum_value", 0.0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class QueryResult:
    """Result of a Data Lake query."""
    query_id: str
    success: bool
    data: List[Dict[str, Any]] = field(default_factory=list)
    total_count: int = 0
    execution_time_ms: float = 0.0
    from_cache: bool = False
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class DataLake:
    """
    CQRS Read-side Data Lake for AsimNexus.
    
    This is the READ/OLAP path. All writes go through VectorMemory.
    The Data Lake periodically snapshots VectorMemory state and
    pre-computes materialized views and aggregations for fast reads.
    
    Key design decisions:
    - Eventual consistency: snapshots are point-in-time, not real-time
    - Read-optimized: materialized views avoid expensive joins at query time
    - Time-series: pre-aggregated metrics for dashboard/reporting
    - Exportable: snapshots can be exported for Mirror Module fine-tuning
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        
        # In-memory stores
        self.snapshots: Dict[str, DataLakeSnapshot] = {}
        self.views: Dict[str, MaterializedView] = {}
        self.aggregations: Dict[str, List[TimeSeriesAggregation]] = {}
        
        # Snapshot sources (registered callbacks to pull data)
        self._snapshot_sources: Dict[SnapshotType, Callable[[], Dict[str, Any]]] = {}
        
        # Load persisted state
        self._load_from_disk()
        
        # Initialize default materialized views
        self._init_default_views()
        
        logger.info("📊 Data Lake initialized")
    
    def _load_from_disk(self) -> None:
        """Load snapshots, views, and aggregations from disk."""
        # Load snapshots
        for snap_file in SNAPSHOTS_PATH.glob("*.json"):
            try:
                with open(snap_file, encoding="utf-8") as f:
                    data = json.load(f)
                    snapshot = DataLakeSnapshot.from_dict(data)
                    self.snapshots[snapshot.snapshot_id] = snapshot
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load snapshot {snap_file.name}: {e}")
        
        # Load materialized views
        for view_file in VIEWS_PATH.glob("*.json"):
            try:
                with open(view_file, encoding="utf-8") as f:
                    data = json.load(f)
                    view = MaterializedView.from_dict(data)
                    self.views[view.view_id] = view
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load view {view_file.name}: {e}")
        
        # Load aggregations
        for agg_file in AGGREGATIONS_PATH.glob("*.json"):
            try:
                with open(agg_file, encoding="utf-8") as f:
                    data = json.load(f)
                    agg = TimeSeriesAggregation.from_dict(data)
                    metric = agg.metric_name
                    if metric not in self.aggregations:
                        self.aggregations[metric] = []
                    self.aggregations[metric].append(agg)
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"Failed to load aggregation {agg_file.name}: {e}")
        
        logger.info(
            f"Loaded {len(self.snapshots)} snapshots, "
            f"{len(self.views)} views, "
            f"{sum(len(v) for v in self.aggregations.values())} aggregations"
        )
    
    def _init_default_views(self) -> None:
        """Initialize default materialized views."""
        default_views = [
            {
                "view_name": "user_activity_summary",
                "query_definition": {
                    "description": "Summary of user activity across all subsystems",
                    "fields": ["user_id", "action_count", "last_active", "top_intents"],
                },
            },
            {
                "view_name": "economy_overview",
                "query_definition": {
                    "description": "Economy health metrics",
                    "fields": ["total_credits", "active_contracts", "marketplace_listings", "token_supply"],
                },
            },
            {
                "view_name": "consensus_health",
                "query_definition": {
                    "description": "Consensus system health metrics",
                    "fields": ["proposals_count", "voter_turnout", "avg_confidence", "pending_arbitrations"],
                },
            },
            {
                "view_name": "mesh_network_status",
                "query_definition": {
                    "description": "Mesh network connectivity and performance",
                    "fields": ["active_nodes", "messages_routed", "avg_latency", "connected_meshes"],
                },
            },
            {
                "view_name": "mirror_evolution_metrics",
                "query_definition": {
                    "description": "Mirror Module self-evolution metrics",
                    "fields": ["reflections_count", "contradiction_rate", "avg_balance_impact", "fine_tune_count"],
                },
            },
        ]
        
        for v_def in default_views:
            view_id = f"view_{v_def['view_name']}"
            if view_id not in self.views:
                view = MaterializedView(
                    view_id=view_id,
                    view_name=v_def["view_name"],
                    query_definition=v_def["query_definition"],
                )
                self.views[view_id] = view
                self._persist_view(view)
    
    def register_snapshot_source(
        self, snapshot_type: SnapshotType, source_fn: Callable[[], Dict[str, Any]]
    ) -> None:
        """Register a callback that provides data for a snapshot type."""
        with self._lock:
            self._snapshot_sources[snapshot_type] = source_fn
            logger.info(f"Registered snapshot source: {snapshot_type.value}")
    
    def take_snapshot(
        self,
        snapshot_type: SnapshotType,
        data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DataLakeSnapshot:
        """
        Take a point-in-time snapshot.
        
        If data is provided, use it directly. Otherwise, try to call
        a registered source function for the snapshot type.
        """
        with self._lock:
            if data is None and snapshot_type in self._snapshot_sources:
                try:
                    data = self._snapshot_sources[snapshot_type]()
                except Exception as e:
                    logger.error(f"Snapshot source failed for {snapshot_type.value}: {e}")
                    data = {"error": str(e)}
            
            if data is None:
                data = {}
            
            # Determine parent snapshot (last snapshot of same type)
            parent_id = None
            for snap in reversed(list(self.snapshots.values())):
                if snap.snapshot_type == snapshot_type:
                    parent_id = snap.snapshot_id
                    break
            
            snapshot = DataLakeSnapshot(
                snapshot_id=f"snap_{snapshot_type.value}_{int(time.time())}_{uuid.uuid4().hex[:8]}",
                snapshot_type=snapshot_type,
                timestamp=time.time(),
                data=data,
                metadata=metadata or {},
                parent_snapshot_id=parent_id,
            )
            
            self.snapshots[snapshot.snapshot_id] = snapshot
            self._persist_snapshot(snapshot)
            
            logger.info(f"📸 Snapshot taken: {snapshot.snapshot_id} ({snapshot_type.value})")
            return snapshot
    
    def get_snapshot(self, snapshot_id: str) -> Optional[DataLakeSnapshot]:
        """Get a specific snapshot by ID."""
        return self.snapshots.get(snapshot_id)
    
    def list_snapshots(
        self,
        snapshot_type: Optional[SnapshotType] = None,
        since: Optional[float] = None,
        limit: int = 100,
    ) -> List[DataLakeSnapshot]:
        """List snapshots with optional filtering."""
        result = list(self.snapshots.values())
        
        if snapshot_type:
            result = [s for s in result if s.snapshot_type == snapshot_type]
        if since:
            result = [s for s in result if s.timestamp >= since]
        
        result.sort(key=lambda s: s.timestamp, reverse=True)
        return result[:limit]
    
    def create_view(
        self,
        view_name: str,
        query_definition: Dict[str, Any],
        initial_data: Optional[Dict[str, Any]] = None,
    ) -> MaterializedView:
        """Create a new materialized view."""
        with self._lock:
            view_id = f"view_{view_name}_{uuid.uuid4().hex[:8]}"
            view = MaterializedView(
                view_id=view_id,
                view_name=view_name,
                data=initial_data or {},
                query_definition=query_definition,
            )
            self.views[view_id] = view
            self._persist_view(view)
            logger.info(f"📊 View created: {view_name} ({view_id})")
            return view
    
    def refresh_view(self, view_id: str, new_data: Dict[str, Any]) -> bool:
        """Refresh a materialized view with new data."""
        with self._lock:
            if view_id not in self.views:
                logger.warning(f"View not found: {view_id}")
                return False
            
            view = self.views[view_id]
            view.data = new_data
            view.last_refreshed = time.time()
            view.row_count = len(new_data) if isinstance(new_data, (list, dict)) else 0
            self._persist_view(view)
            return True
    
    def get_view(self, view_name: str) -> Optional[MaterializedView]:
        """Get a materialized view by name."""
        for view in self.views.values():
            if view.view_name == view_name:
                return view
        return None
    
    def list_views(self) -> List[MaterializedView]:
        """List all materialized views."""
        return list(self.views.values())
    
    def record_aggregation(
        self,
        metric_name: str,
        value: float,
        granularity: AggregationGranularity = AggregationGranularity.DAILY,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TimeSeriesAggregation:
        """Record a time-series data point."""
        with self._lock:
            now = datetime.utcnow()
            
            # Compute time bucket based on granularity
            if granularity == AggregationGranularity.HOURLY:
                time_bucket = now.strftime("%Y-%m-%dT%H:00:00")
            elif granularity == AggregationGranularity.DAILY:
                time_bucket = now.strftime("%Y-%m-%d")
            elif granularity == AggregationGranularity.WEEKLY:
                # ISO week
                iso_year, iso_week, _ = now.isocalendar()
                time_bucket = f"{iso_year}-W{iso_week:02d}"
            elif granularity == AggregationGranularity.MONTHLY:
                time_bucket = now.strftime("%Y-%m")
            else:
                time_bucket = now.strftime("%Y-%m-%d")
            
            # Check if we already have an aggregation for this bucket
            existing = None
            if metric_name in self.aggregations:
                for agg in self.aggregations[metric_name]:
                    if agg.time_bucket == time_bucket and agg.granularity == granularity:
                        existing = agg
                        break
            
            if existing:
                # Update existing aggregation
                existing.count += 1
                existing.sum_value += value
                existing.value = existing.sum_value / existing.count  # average
                existing.min_value = min(existing.min_value, value)
                existing.max_value = max(existing.max_value, value)
                if metadata:
                    existing.metadata.update(metadata)
                agg = existing
            else:
                # Create new aggregation
                agg = TimeSeriesAggregation(
                    aggregation_id=f"agg_{metric_name}_{time_bucket}_{uuid.uuid4().hex[:8]}",
                    metric_name=metric_name,
                    granularity=granularity,
                    time_bucket=time_bucket,
                    value=value,
                    count=1,
                    min_value=value,
                    max_value=value,
                    sum_value=value,
                    metadata=metadata or {},
                )
                if metric_name not in self.aggregations:
                    self.aggregations[metric_name] = []
                self.aggregations[metric_name].append(agg)
            
            self._persist_aggregation(agg)
            return agg
    
    def query_aggregation(
        self,
        metric_name: str,
        granularity: Optional[AggregationGranularity] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        limit: int = 100,
    ) -> List[TimeSeriesAggregation]:
        """Query time-series aggregations."""
        with self._lock:
            results = list(self.aggregations.get(metric_name, []))
            
            if granularity:
                results = [a for a in results if a.granularity == granularity]
            if since:
                results = [a for a in results if a.time_bucket >= since]
            if until:
                results = [a for a in results if a.time_bucket <= until]
            
            results.sort(key=lambda a: a.time_bucket, reverse=True)
            return results[:limit]
    
    def query(
        self,
        query_type: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> QueryResult:
        """
        Main query interface for the Data Lake (CQRS read side).
        
        Supported query types:
        - "snapshot_latest": Get latest snapshot of a type
        - "snapshot_range": Get snapshots in a time range
        - "view": Get a materialized view
        - "aggregation": Query time-series aggregations
        - "export": Export data for Mirror Module fine-tuning
        """
        start_time = time.time()
        query_id = f"query_{uuid.uuid4().hex[:12]}"
        params = params or {}
        
        try:
            if query_type == "snapshot_latest":
                snap_type_str = params.get("snapshot_type", "")
                try:
                    snap_type = SnapshotType(snap_type_str)
                except ValueError:
                    return QueryResult(
                        query_id=query_id,
                        success=False,
                        error=f"Invalid snapshot_type: {snap_type_str}",
                    )
                
                snapshots = self.list_snapshots(snapshot_type=snap_type, limit=1)
                if snapshots:
                    return QueryResult(
                        query_id=query_id,
                        success=True,
                        data=[snapshots[0].to_dict()],
                        total_count=1,
                        execution_time_ms=(time.time() - start_time) * 1000,
                        from_cache=False,
                    )
                return QueryResult(
                    query_id=query_id,
                    success=True,
                    data=[],
                    total_count=0,
                    execution_time_ms=(time.time() - start_time) * 1000,
                )
            
            elif query_type == "snapshot_range":
                snap_type_str = params.get("snapshot_type", "")
                since = params.get("since")
                limit = params.get("limit", 100)
                
                try:
                    snap_type = SnapshotType(snap_type_str) if snap_type_str else None
                except ValueError:
                    snap_type = None
                
                snapshots = self.list_snapshots(
                    snapshot_type=snap_type,
                    since=since,
                    limit=limit,
                )
                return QueryResult(
                    query_id=query_id,
                    success=True,
                    data=[s.to_dict() for s in snapshots],
                    total_count=len(snapshots),
                    execution_time_ms=(time.time() - start_time) * 1000,
                    from_cache=False,
                )
            
            elif query_type == "view":
                view_name = params.get("view_name", "")
                view = self.get_view(view_name)
                if view:
                    return QueryResult(
                        query_id=query_id,
                        success=True,
                        data=[view.to_dict()],
                        total_count=1,
                        execution_time_ms=(time.time() - start_time) * 1000,
                        from_cache=True,
                    )
                return QueryResult(
                    query_id=query_id,
                    success=False,
                    error=f"View not found: {view_name}",
                    execution_time_ms=(time.time() - start_time) * 1000,
                )
            
            elif query_type == "aggregation":
                metric_name = params.get("metric_name", "")
                granularity_str = params.get("granularity", "")
                since = params.get("since")
                until = params.get("until")
                limit = params.get("limit", 100)
                
                try:
                    granularity = AggregationGranularity(granularity_str) if granularity_str else None
                except ValueError:
                    granularity = None
                
                results = self.query_aggregation(
                    metric_name=metric_name,
                    granularity=granularity,
                    since=since,
                    until=until,
                    limit=limit,
                )
                return QueryResult(
                    query_id=query_id,
                    success=True,
                    data=[a.to_dict() for a in results],
                    total_count=len(results),
                    execution_time_ms=(time.time() - start_time) * 1000,
                    from_cache=True,
                )
            
            elif query_type == "export":
                """Export data for Mirror Module fine-tuning."""
                export_format = params.get("format", "json")
                snapshot_types = params.get("snapshot_types", [])
                limit = params.get("limit", 1000)
                
                export_data = []
                for snap in list(self.snapshots.values())[:limit]:
                    if not snapshot_types or snap.snapshot_type.value in snapshot_types:
                        export_data.append({
                            "snapshot_id": snap.snapshot_id,
                            "type": snap.snapshot_type.value,
                            "timestamp": snap.timestamp,
                            "data": snap.data,
                            "metadata": snap.metadata,
                        })
                
                return QueryResult(
                    query_id=query_id,
                    success=True,
                    data=export_data,
                    total_count=len(export_data),
                    execution_time_ms=(time.time() - start_time) * 1000,
                    from_cache=False,
                    metadata={"export_format": export_format},
                )
            
            else:
                return QueryResult(
                    query_id=query_id,
                    success=False,
                    error=f"Unknown query type: {query_type}",
                    execution_time_ms=(time.time() - start_time) * 1000,
                )
        
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return QueryResult(
                query_id=query_id,
                success=False,
                error=str(e),
                execution_time_ms=(time.time() - start_time) * 1000,
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Data Lake statistics."""
        with self._lock:
            total_aggregations = sum(len(v) for v in self.aggregations.values())
            
            # Compute oldest and newest snapshot times
            timestamps = [s.timestamp for s in self.snapshots.values()]
            oldest = min(timestamps) if timestamps else 0
            newest = max(timestamps) if timestamps else 0
            
            return {
                "total_snapshots": len(self.snapshots),
                "total_views": len(self.views),
                "total_aggregations": total_aggregations,
                "unique_metrics": len(self.aggregations),
                "oldest_snapshot": oldest,
                "newest_snapshot": newest,
                "data_age_hours": (time.time() - oldest) / 3600 if oldest else 0,
                "snapshot_types": {
                    st.value: sum(1 for s in self.snapshots.values() if s.snapshot_type == st)
                    for st in SnapshotType
                },
                "views": [v.view_name for v in self.views.values()],
            }
    
    def _persist_snapshot(self, snapshot: DataLakeSnapshot) -> None:
        """Persist a snapshot to disk."""
        try:
            filepath = SNAPSHOTS_PATH / f"{snapshot.snapshot_id}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(snapshot.to_dict(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to persist snapshot {snapshot.snapshot_id}: {e}")
    
    def _persist_view(self, view: MaterializedView) -> None:
        """Persist a materialized view to disk."""
        try:
            filepath = VIEWS_PATH / f"{view.view_id}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(view.to_dict(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to persist view {view.view_id}: {e}")
    
    def _persist_aggregation(self, agg: TimeSeriesAggregation) -> None:
        """Persist an aggregation to disk."""
        try:
            filepath = AGGREGATIONS_PATH / f"{agg.aggregation_id}.json"
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(agg.to_dict(), f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to persist aggregation {agg.aggregation_id}: {e}")


# ─── Singleton ───────────────────────────────────────────────────────────────

_data_lake_instance: Optional[DataLake] = None
_data_lake_lock = threading.Lock()


def get_data_lake() -> DataLake:
    """Get the global Data Lake singleton."""
    global _data_lake_instance
    if _data_lake_instance is None:
        with _data_lake_lock:
            if _data_lake_instance is None:
                _data_lake_instance = DataLake()
    return _data_lake_instance


def reset_data_lake() -> None:
    """Reset the Data Lake singleton (for testing)."""
    global _data_lake_instance
    with _data_lake_lock:
        _data_lake_instance = None
