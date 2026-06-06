#!/usr/bin/env python3
"""Node Registry -- trust registry for mesh network nodes."""
import json, os, sqlite3, threading, time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

__all__ = ["TrustLevel","NodeStatus","NodeRecord","TrustEvent","NodeRegistry",
           "get_node_registry","reset_node_registry"]

class TrustLevel(Enum):
    UNKNOWN="unknown"; LOW="low"; MEDIUM="medium"; HIGH="high"
    CRITICAL="critical"; TRUSTED="trusted"; UNTRUSTED="untrusted"

class NodeStatus(Enum):
    ONLINE="online"; OFFLINE="offline"; SUSPENDED="suspended"; BANNED="banned"

def _to_timestamp(val):
    """Convert ISO datetime string or float to float timestamp (UTC)."""
    if isinstance(val, str):
        try:
            dt = datetime.fromisoformat(val.replace("Z","+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except:
            pass
    return val

@dataclass
class NodeRecord:
    node_id:str; hostname:Optional[str]=None; ip_address:Optional[str]=None
    port:Optional[int]=None; public_key:Optional[str]=None
    capabilities:Optional[List[str]]=None; version:Optional[str]=None
    trust_level:TrustLevel=TrustLevel.UNKNOWN; status:NodeStatus=NodeStatus.ONLINE
    last_seen:Optional[float]=None; first_seen:Optional[float]=None
    last_contact:Optional[float]=None
    def to_dict(self)->Dict[str,Any]:
        d=asdict(self)
        d["trust_level"]=self.trust_level.value; d["status"]=self.status.value
        return d

@dataclass
class TrustEvent:
    event_type:str; node_id:str; timestamp:float
    old_trust:Optional[str]=None; new_trust:Optional[str]=None; reason:str=""

class NodeRegistry:
    def __init__(self,db_path:Optional[str]=None,use_memory:bool=False):
        self._use_memory=use_memory
        if use_memory:
            self._db_path=":memory:"
        elif db_path:
            self._db_path=db_path
        else:
            self._db_path=os.environ.get("ASIM_MESH_NODE_REGISTRY_DB","data/node_registry.db")
        self._lock=threading.Lock()
        self._mem_conn:Optional[sqlite3.Connection]=None
        self._last_ts:float=0.0
        self._nodes_cache:Optional[Dict[str,NodeRecord]]=None
        self._init_db()

    @property
    def db_path(self) -> str:
        """Expose db_path for tests."""
        return self._db_path

    def _now(self)->float:
        t=time.time()
        if t<=self._last_ts: t=self._last_ts+0.0001
        self._last_ts=t
        return t

    def _get_conn(self)->sqlite3.Connection:
        if self._use_memory:
            if self._mem_conn is None: self._mem_conn=sqlite3.connect(self._db_path)
            return self._mem_conn
        return sqlite3.connect(self._db_path)

    def _close_conn(self)->None:
        if self._mem_conn is not None:
            try: self._mem_conn.close()
            except Exception: pass
            self._mem_conn=None

    def _invalidate_cache(self)->None:
        self._nodes_cache=None

    def _init_db(self)->None:
        conn=self._get_conn()
        try:
            conn.execute("PRAGMA journal_mode=WAL"); conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("CREATE TABLE IF NOT EXISTS nodes (node_id TEXT PRIMARY KEY,hostname TEXT,ip_address TEXT,port INTEGER,public_key TEXT,capabilities TEXT,version TEXT,trust_level TEXT NOT NULL DEFAULT 'unknown',status TEXT NOT NULL DEFAULT 'online',last_seen REAL,first_seen REAL NOT NULL,last_contact REAL)")
            conn.execute("CREATE TABLE IF NOT EXISTS trust_events (id INTEGER PRIMARY KEY AUTOINCREMENT,event_type TEXT NOT NULL,node_id TEXT NOT NULL,timestamp REAL NOT NULL,old_trust TEXT,new_trust TEXT,reason TEXT NOT NULL,FOREIGN KEY(node_id) REFERENCES nodes(node_id))")
            conn.commit()
        finally:
            if not self._use_memory: conn.close()

    def register_node(self,node_id:str,hostname:Optional[str]=None,
                      ip_address:Optional[str]=None,port:Optional[int]=None,
                      public_key:Optional[str]=None,
                      capabilities:Optional[List[str]]=None,
                      version:Optional[str]=None)->NodeRecord:
        now=self._now(); caps_json=json.dumps(capabilities or [])
        conn=self._get_conn()
        try:
            existing=conn.execute("SELECT * FROM nodes WHERE node_id=?",(node_id,)).fetchone()
            if existing:
                conn.execute("UPDATE nodes SET hostname=COALESCE(?,hostname),ip_address=COALESCE(?,ip_address),port=COALESCE(?,port),public_key=COALESCE(?,public_key),capabilities=COALESCE(?,capabilities),version=COALESCE(?,version),last_seen=?,last_contact=? WHERE node_id=?",(hostname,ip_address,port,public_key,caps_json,version,now,now,node_id))
            else:
                conn.execute("INSERT INTO nodes(node_id,hostname,ip_address,port,public_key,capabilities,version,trust_level,status,last_seen,first_seen,last_contact) VALUES(?,?,?,?,?,?,?,'unknown','online',?,?,?)",(node_id,hostname,ip_address,port,public_key,caps_json,version,now,now,now))
                conn.execute("INSERT INTO trust_events(event_type,node_id,timestamp,old_trust,new_trust,reason) VALUES('discovery',?,?,NULL,'unknown','Node discovered and registered')",(node_id,now))
            conn.commit()
            self._invalidate_cache()
            return self.get_node(node_id)
        finally:
            if not self._use_memory: conn.close()

    def get_node(self,node_id:str)->Optional[NodeRecord]:
        if self._nodes_cache is not None and node_id in self._nodes_cache:
            return self._nodes_cache[node_id]
        conn=self._get_conn()
        try:
            row=conn.execute("SELECT * FROM nodes WHERE node_id=?",(node_id,)).fetchone()
            return None if row is None else self._row_to_record(row)
        finally:
            if not self._use_memory: conn.close()

    def get_nodes_by_trust(self,trust_level:TrustLevel)->List[NodeRecord]:
        conn=self._get_conn()
        try:
            return [self._row_to_record(r) for r in conn.execute("SELECT * FROM nodes WHERE trust_level=?",(trust_level.value,)).fetchall()]
        finally:
            if not self._use_memory: conn.close()

    def get_nodes_by_status(self,status:NodeStatus)->List[NodeRecord]:
        conn=self._get_conn()
        try:
            return [self._row_to_record(r) for r in conn.execute("SELECT * FROM nodes WHERE status=?",(status.value,)).fetchall()]
        finally:
            if not self._use_memory: conn.close()

    def get_online_nodes(self)->List[NodeRecord]:
        return self.get_nodes_by_status(NodeStatus.ONLINE)

    @property
    def nodes(self)->Dict[str,NodeRecord]:
        if self._nodes_cache is not None:
            return self._nodes_cache
        conn=self._get_conn()
        try:
            self._nodes_cache={r[0]:self._row_to_record(r) for r in conn.execute("SELECT * FROM nodes").fetchall()}
            return self._nodes_cache
        finally:
            if not self._use_memory: conn.close()

    def set_trust_level(self,node_id:str,trust_level:TrustLevel,reason:str="")->bool:
        conn=self._get_conn()
        try:
            row=conn.execute("SELECT trust_level FROM nodes WHERE node_id=?",(node_id,)).fetchone()
            if row is None: return False
            old_trust=row[0]; now=self._now()
            conn.execute("UPDATE nodes SET trust_level=? WHERE node_id=?",(trust_level.value,node_id))
            conn.execute("INSERT INTO trust_events(event_type,node_id,timestamp,old_trust,new_trust,reason) VALUES('trust_change',?,?,?,?,?)",(node_id,now,old_trust,trust_level.value,reason))
            conn.commit()
            self._invalidate_cache()
            return True
        finally:
            if not self._use_memory: conn.close()

    def suspend_node(self,node_id:str,reason:str="")->bool:
        return self._set_status(node_id,NodeStatus.SUSPENDED,reason)

    def ban_node(self,node_id:str,reason:str="")->bool:
        conn=self._get_conn()
        try:
            row=conn.execute("SELECT * FROM nodes WHERE node_id=?",(node_id,)).fetchone()
            if row is None: return False
            now=self._now()
            conn.execute("UPDATE nodes SET status=?,trust_level=? WHERE node_id=?",(NodeStatus.BANNED.value,TrustLevel.UNTRUSTED.value,node_id))
            conn.execute("INSERT INTO trust_events(event_type,node_id,timestamp,old_trust,new_trust,reason) VALUES('ban',?,?,?,?,?)",(node_id,now,TrustLevel.UNTRUSTED.value,row[6],reason))
            conn.commit()
            self._invalidate_cache()
            return True
        finally:
            if not self._use_memory: conn.close()

    def unban_node(self,node_id:str,reason:str="")->bool:
        conn=self._get_conn()
        try:
            row=conn.execute("SELECT * FROM nodes WHERE node_id=?",(node_id,)).fetchone()
            if row is None: return False
            now=self._now()
            conn.execute("UPDATE nodes SET status=?,trust_level=? WHERE node_id=?",(NodeStatus.ONLINE.value,TrustLevel.LOW.value,node_id))
            conn.execute("INSERT INTO trust_events(event_type,node_id,timestamp,old_trust,new_trust,reason) VALUES('unban',?,?,?,?,?)",(node_id,now,row[6],TrustLevel.LOW.value,reason))
            conn.commit()
            self._invalidate_cache()
            return True
        finally:
            if not self._use_memory: conn.close()

    def _set_status(self,node_id:str,status:NodeStatus,reason:str="")->bool:
        conn=self._get_conn()
        try:
            row=conn.execute("SELECT * FROM nodes WHERE node_id=?",(node_id,)).fetchone()
            if row is None: return False
            conn.execute("UPDATE nodes SET status=? WHERE node_id=?",(status.value,node_id))
            conn.commit()
            self._invalidate_cache()
            return True
        finally:
            if not self._use_memory: conn.close()

    def update_last_seen(self,node_id:str)->bool:
        now=self._now()
        conn=self._get_conn()
        try:
            row=conn.execute("SELECT * FROM nodes WHERE node_id=?",(node_id,)).fetchone()
            if row is None: return False
            conn.execute("UPDATE nodes SET last_seen=?,last_contact=? WHERE node_id=?",(now,now,node_id))
            conn.commit()
            self._invalidate_cache()
            return True
        finally:
            if not self._use_memory: conn.close()

    def _persist_node(self,node:NodeRecord)->None:
        last_seen=_to_timestamp(node.last_seen) if node.last_seen is not None else None
        first_seen=_to_timestamp(node.first_seen) if node.first_seen is not None else None
        last_contact=_to_timestamp(node.last_contact) if node.last_contact is not None else None
        conn=self._get_conn()
        try:
            conn.execute("UPDATE nodes SET hostname=?,ip_address=?,port=?,public_key=?,capabilities=?,version=?,trust_level=?,status=?,last_seen=?,first_seen=?,last_contact=? WHERE node_id=?",(node.hostname,node.ip_address,node.port,node.public_key,json.dumps(node.capabilities or []),node.version,node.trust_level.value,node.status.value,last_seen,first_seen,last_contact,node.node_id))
            conn.commit()
            self._invalidate_cache()
        finally:
            if not self._use_memory: conn.close()

    def cleanup_stale_nodes(self,max_age_seconds:Optional[int]=None)->List[str]:
        if max_age_seconds is None: max_age_seconds=300
        cutoff=time.time()-max_age_seconds
        conn=self._get_conn()
        try:
            all_nodes=conn.execute("SELECT node_id,last_seen FROM nodes WHERE status='online' AND last_seen IS NOT NULL").fetchall()
            stale_ids=[]
            for node_id,ls in all_nodes:
                ts=_to_timestamp(ls)
                if ts is not None and ts<cutoff:
                    stale_ids.append(node_id)
            for sid in stale_ids:
                conn.execute("UPDATE nodes SET status='offline' WHERE node_id=?",(sid,))
            conn.commit()
            self._invalidate_cache()
            return stale_ids
        finally:
            if not self._use_memory: conn.close()

    def get_trust_events(self,node_id:Optional[str]=None,limit:Optional[int]=None)->List[TrustEvent]:
        conn=self._get_conn()
        try:
            if node_id:
                rows=conn.execute("SELECT event_type,node_id,timestamp,old_trust,new_trust,reason FROM trust_events WHERE node_id=? ORDER BY timestamp DESC",(node_id,)).fetchall()
            else:
                rows=conn.execute("SELECT event_type,node_id,timestamp,old_trust,new_trust,reason FROM trust_events ORDER BY timestamp DESC").fetchall()
            result=[TrustEvent(event_type=r[0],node_id=r[1],timestamp=r[2],old_trust=r[3],new_trust=r[4],reason=r[5]) for r in rows]
            if limit is not None: result=result[:limit]
            return result
        finally:
            if not self._use_memory: conn.close()

    def get_stats(self)->Dict[str,Any]:
        conn=self._get_conn()
        try:
            total=conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
            online=conn.execute("SELECT COUNT(*) FROM nodes WHERE status='online'").fetchone()[0]
            offline=conn.execute("SELECT COUNT(*) FROM nodes WHERE status='offline'").fetchone()[0]
            by_trust=dict(conn.execute("SELECT trust_level,COUNT(*) FROM nodes GROUP BY trust_level").fetchall())
            by_status=dict(conn.execute("SELECT status,COUNT(*) FROM nodes GROUP BY status").fetchall())
            events=conn.execute("SELECT COUNT(*) FROM trust_events").fetchone()[0]
            return {"total_nodes":total,"online_nodes":online,"offline_nodes":offline,
                    "by_trust_level":by_trust,"by_status":by_status,"total_trust_events":events}
        finally:
            if not self._use_memory: conn.close()

    @staticmethod
    def _row_to_record(row)->NodeRecord:
        if hasattr(row,"keys"):
            def g(k): return row[k]
        else:
            ks=["node_id","hostname","ip_address","port","public_key","capabilities","version","trust_level","status","last_seen","first_seen","last_contact"]
            def g(k): return row[ks.index(k)]
        caps_raw=g("capabilities")
        return NodeRecord(node_id=g("node_id"),hostname=g("hostname"),ip_address=g("ip_address"),port=g("port"),public_key=g("public_key"),capabilities=json.loads(caps_raw) if caps_raw else [],version=g("version"),trust_level=TrustLevel(g("trust_level")),status=NodeStatus(g("status")),last_seen=g("last_seen"),first_seen=g("first_seen"),last_contact=g("last_contact"))

_registry_instance:Optional[NodeRegistry]=None
_registry_lock=threading.Lock()

def get_node_registry(db_path:Optional[str]=None,use_memory:bool=False)->NodeRegistry:
    global _registry_instance
    if _registry_instance is None:
        with _registry_lock:
            if _registry_instance is None:
                _registry_instance=NodeRegistry(db_path=db_path,use_memory=use_memory)
    return _registry_instance

def reset_node_registry()->None:
    global _registry_instance
    with _registry_lock:
        if _registry_instance is not None:
            _registry_instance._close_conn()
            _registry_instance=None
