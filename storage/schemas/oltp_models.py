"""
AsimNexus Storage — OLTP Table Model Definitions.

Defines all 10 OLTP tables as dataclass-based models with dual SQL dialects
(PostgreSQL and SQLite), used by ``OltpEngine`` for schema creation and
migration. These are NOT SQLAlchemy models — they are plain dataclasses
with DDL strings for maximum portability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# OltpTable — Single table descriptor
# ---------------------------------------------------------------------------


@dataclass
class OltpTable:
    """Describes a single OLTP table with dual-dialect DDL."""

    name: str
    ddl_postgres: str
    ddl_sqlite: str
    columns: List[Dict[str, str]] = field(default_factory=list)
    indexes: List[str] = field(default_factory=list)


# ===================================================================
# Table 1: users
# ===================================================================

USERS_TABLE = OltpTable(
    name="users",
    ddl_postgres="""CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(128) UNIQUE NOT NULL,
    email VARCHAR(256) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    display_name VARCHAR(256),
    avatar_url VARCHAR(1024),
    role VARCHAR(64) DEFAULT 'user',
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    preferences JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}'
)""",
    ddl_sqlite="""CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    display_name TEXT,
    avatar_url TEXT,
    role TEXT DEFAULT 'user',
    is_active INTEGER DEFAULT 1,
    is_verified INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    last_login TEXT,
    preferences TEXT DEFAULT '{}',
    metadata TEXT DEFAULT '{}'
)""",
    columns=[
        {"name": "id", "type": "UUID/TEXT", "nullable": False, "pk": True},
        {"name": "username", "type": "VARCHAR(128)/TEXT", "nullable": False, "unique": True},
        {"name": "email", "type": "VARCHAR(256)/TEXT", "nullable": False, "unique": True},
        {"name": "password_hash", "type": "VARCHAR(256)/TEXT", "nullable": False},
        {"name": "display_name", "type": "VARCHAR(256)/TEXT"},
        {"name": "avatar_url", "type": "VARCHAR(1024)/TEXT"},
        {"name": "role", "type": "VARCHAR(64)/TEXT", "default": "user"},
        {"name": "is_active", "type": "BOOLEAN/INTEGER", "default": True},
        {"name": "is_verified", "type": "BOOLEAN/INTEGER", "default": False},
        {"name": "created_at", "type": "TIMESTAMPTZ/TEXT"},
        {"name": "updated_at", "type": "TIMESTAMPTZ/TEXT"},
        {"name": "last_login", "type": "TIMESTAMPTZ/TEXT"},
        {"name": "preferences", "type": "JSONB/TEXT"},
        {"name": "metadata", "type": "JSONB/TEXT"},
    ],
    indexes=[
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
    ],
)

# ===================================================================
# Table 2: sessions
# ===================================================================

SESSIONS_TABLE = OltpTable(
    name="sessions",
    ddl_postgres="""CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    token VARCHAR(512) UNIQUE NOT NULL,
    ip_address VARCHAR(64),
    user_agent TEXT,
    device_id VARCHAR(256),
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    last_activity TIMESTAMPTZ
)""",
    ddl_sqlite="""CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    token TEXT UNIQUE NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    device_id TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT,
    last_activity TEXT
)""",
    columns=[
        {"name": "id", "type": "UUID/TEXT", "nullable": False, "pk": True},
        {"name": "user_id", "type": "UUID/TEXT", "nullable": False, "fk": "users(id)"},
        {"name": "token", "type": "VARCHAR(512)/TEXT", "nullable": False, "unique": True},
        {"name": "ip_address", "type": "VARCHAR(64)/TEXT"},
        {"name": "user_agent", "type": "TEXT/TEXT"},
        {"name": "device_id", "type": "VARCHAR(256)/TEXT"},
        {"name": "is_active", "type": "BOOLEAN/INTEGER", "default": True},
        {"name": "created_at", "type": "TIMESTAMPTZ/TEXT"},
        {"name": "expires_at", "type": "TIMESTAMPTZ/TEXT"},
        {"name": "last_activity", "type": "TIMESTAMPTZ/TEXT"},
    ],
    indexes=[
        "CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token)",
    ],
)

# ===================================================================
# Table 3: credit_accounts  (CRITICAL — fixes RAM-only economy)
# ===================================================================

CREDIT_ACCOUNTS_TABLE = OltpTable(
    name="credit_accounts",
    ddl_postgres="""CREATE TABLE IF NOT EXISTS credit_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    account_type VARCHAR(64) NOT NULL DEFAULT 'user',
    balance DECIMAL(24,8) NOT NULL DEFAULT 0.0,
    currency VARCHAR(16) DEFAULT 'ASIM',
    credit_limit DECIMAL(24,8) DEFAULT 0.0,
    is_frozen BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
)""",
    ddl_sqlite="""CREATE TABLE IF NOT EXISTS credit_accounts (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    account_type TEXT NOT NULL DEFAULT 'user',
    balance REAL NOT NULL DEFAULT 0.0,
    currency TEXT DEFAULT 'ASIM',
    credit_limit REAL DEFAULT 0.0,
    is_frozen INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    metadata TEXT DEFAULT '{}'
)""",
    columns=[
        {"name": "id", "type": "UUID/TEXT", "nullable": False, "pk": True},
        {"name": "user_id", "type": "UUID/TEXT", "fk": "users(id)"},
        {"name": "account_type", "type": "VARCHAR(64)/TEXT", "nullable": False, "default": "user"},
        {"name": "balance", "type": "DECIMAL(24,8)/REAL", "nullable": False, "default": 0.0},
        {"name": "currency", "type": "VARCHAR(16)/TEXT", "default": "ASIM"},
        {"name": "credit_limit", "type": "DECIMAL(24,8)/REAL", "default": 0.0},
        {"name": "is_frozen", "type": "BOOLEAN/INTEGER", "default": False},
        {"name": "created_at", "type": "TIMESTAMPTZ/TEXT"},
        {"name": "updated_at", "type": "TIMESTAMPTZ/TEXT"},
        {"name": "metadata", "type": "JSONB/TEXT"},
    ],
    indexes=[
        "CREATE INDEX IF NOT EXISTS idx_credit_accounts_user_id ON credit_accounts(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_credit_accounts_type ON credit_accounts(account_type)",
    ],
)

# ===================================================================
# Table 4: credit_transactions
# ===================================================================

CREDIT_TRANSACTIONS_TABLE = OltpTable(
    name="credit_transactions",
    ddl_postgres="""CREATE TABLE IF NOT EXISTS credit_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES credit_accounts(id),
    transaction_type VARCHAR(64) NOT NULL,
    amount DECIMAL(24,8) NOT NULL,
    balance_before DECIMAL(24,8) NOT NULL,
    balance_after DECIMAL(24,8) NOT NULL,
    reference_type VARCHAR(128),
    reference_id VARCHAR(256),
    description TEXT,
    initiated_by VARCHAR(256),
    status VARCHAR(64) DEFAULT 'completed',
    created_at TIMESTAMPTZ DEFAULT NOW()
)""",
    ddl_sqlite="""CREATE TABLE IF NOT EXISTS credit_transactions (
    id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL REFERENCES credit_accounts(id),
    transaction_type TEXT NOT NULL,
    amount REAL NOT NULL,
    balance_before REAL NOT NULL,
    balance_after REAL NOT NULL,
    reference_type TEXT,
    reference_id TEXT,
    description TEXT,
    initiated_by TEXT,
    status TEXT DEFAULT 'completed',
    created_at TEXT DEFAULT (datetime('now'))
)""",
    columns=[
        {"name": "id", "type": "UUID/TEXT", "nullable": False, "pk": True},
        {"name": "account_id", "type": "UUID/TEXT", "nullable": False, "fk": "credit_accounts(id)"},
        {"name": "transaction_type", "type": "VARCHAR(64)/TEXT", "nullable": False},
        {"name": "amount", "type": "DECIMAL(24,8)/REAL", "nullable": False},
        {"name": "balance_before", "type": "DECIMAL(24,8)/REAL", "nullable": False},
        {"name": "balance_after", "type": "DECIMAL(24,8)/REAL", "nullable": False},
        {"name": "reference_type", "type": "VARCHAR(128)/TEXT"},
        {"name": "reference_id", "type": "VARCHAR(256)/TEXT"},
        {"name": "description", "type": "TEXT/TEXT"},
        {"name": "initiated_by", "type": "VARCHAR(256)/TEXT"},
        {"name": "status", "type": "VARCHAR(64)/TEXT", "default": "completed"},
        {"name": "created_at", "type": "TIMESTAMPTZ/TEXT"},
    ],
    indexes=[
        "CREATE INDEX IF NOT EXISTS idx_credit_tx_account_id ON credit_transactions(account_id)",
        "CREATE INDEX IF NOT EXISTS idx_credit_tx_type ON credit_transactions(transaction_type)",
        "CREATE INDEX IF NOT EXISTS idx_credit_tx_status ON credit_transactions(status)",
        "CREATE INDEX IF NOT EXISTS idx_credit_tx_created ON credit_transactions(created_at)",
    ],
)

# ===================================================================
# Table 5: governance_state  (CRITICAL — fixes in-memory blockchain)
# ===================================================================

GOVERNANCE_STATE_TABLE = OltpTable(
    name="governance_state",
    ddl_postgres="""CREATE TABLE IF NOT EXISTS governance_state (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    block_number BIGINT NOT NULL,
    previous_hash VARCHAR(128),
    hash VARCHAR(128) NOT NULL,
    transactions JSONB DEFAULT '[]',
    governance_type VARCHAR(64),
    proposal_id VARCHAR(256),
    status VARCHAR(64) DEFAULT 'pending',
    approved_by JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    executed_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
)""",
    ddl_sqlite="""CREATE TABLE IF NOT EXISTS governance_state (
    id TEXT PRIMARY KEY,
    block_number INTEGER NOT NULL,
    previous_hash TEXT,
    hash TEXT NOT NULL,
    transactions TEXT DEFAULT '[]',
    governance_type TEXT,
    proposal_id TEXT,
    status TEXT DEFAULT 'pending',
    approved_by TEXT DEFAULT '[]',
    created_at TEXT DEFAULT (datetime('now')),
    executed_at TEXT,
    metadata TEXT DEFAULT '{}'
)""",
    columns=[
        {"name": "id", "type": "UUID/TEXT", "nullable": False, "pk": True},
        {"name": "block_number", "type": "BIGINT/INTEGER", "nullable": False},
        {"name": "previous_hash", "type": "VARCHAR(128)/TEXT"},
        {"name": "hash", "type": "VARCHAR(128)/TEXT", "nullable": False},
        {"name": "transactions", "type": "JSONB/TEXT"},
        {"name": "governance_type", "type": "VARCHAR(64)/TEXT"},
        {"name": "proposal_id", "type": "VARCHAR(256)/TEXT"},
        {"name": "status", "type": "VARCHAR(64)/TEXT", "default": "pending"},
        {"name": "approved_by", "type": "JSONB/TEXT"},
        {"name": "created_at", "type": "TIMESTAMPTZ/TEXT"},
        {"name": "executed_at", "type": "TIMESTAMPTZ/TEXT"},
        {"name": "metadata", "type": "JSONB/TEXT"},
    ],
    indexes=[
        "CREATE INDEX IF NOT EXISTS idx_gov_state_block ON governance_state(block_number)",
        "CREATE INDEX IF NOT EXISTS idx_gov_state_type ON governance_state(governance_type)",
        "CREATE INDEX IF NOT EXISTS idx_gov_state_status ON governance_state(status)",
        "CREATE INDEX IF NOT EXISTS idx_gov_state_proposal ON governance_state(proposal_id)",
    ],
)

# ===================================================================
# Table 6: governance_decisions  (audit trail for all governance actions)
# ===================================================================

GOVERNANCE_DECISIONS_TABLE = OltpTable(
    name="governance_decisions",
    ddl_postgres="""CREATE TABLE IF NOT EXISTS governance_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_type VARCHAR(64) NOT NULL,
    initiator_id VARCHAR(256),
    initiator_type VARCHAR(64),
    target_sector VARCHAR(128),
    action VARCHAR(256),
    verdict VARCHAR(64),
    reasoning TEXT,
    vote_breakdown JSONB,
    dharma_weight FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW()
)""",
    ddl_sqlite="""CREATE TABLE IF NOT EXISTS governance_decisions (
    id TEXT PRIMARY KEY,
    decision_type TEXT NOT NULL,
    initiator_id TEXT,
    initiator_type TEXT,
    target_sector TEXT,
    action TEXT,
    verdict TEXT,
    reasoning TEXT,
    vote_breakdown TEXT,
    dharma_weight REAL,
    created_at TEXT DEFAULT (datetime('now'))
)""",
    columns=[
        {"name": "id", "type": "UUID/TEXT", "nullable": False, "pk": True},
        {"name": "decision_type", "type": "VARCHAR(64)/TEXT", "nullable": False},
        {"name": "initiator_id", "type": "VARCHAR(256)/TEXT"},
        {"name": "initiator_type", "type": "VARCHAR(64)/TEXT"},
        {"name": "target_sector", "type": "VARCHAR(128)/TEXT"},
        {"name": "action", "type": "VARCHAR(256)/TEXT"},
        {"name": "verdict", "type": "VARCHAR(64)/TEXT"},
        {"name": "reasoning", "type": "TEXT/TEXT"},
        {"name": "vote_breakdown", "type": "JSONB/TEXT"},
        {"name": "dharma_weight", "type": "FLOAT/REAL"},
        {"name": "created_at", "type": "TIMESTAMPTZ/TEXT"},
    ],
    indexes=[
        "CREATE INDEX IF NOT EXISTS idx_gov_decisions_type ON governance_decisions(decision_type)",
        "CREATE INDEX IF NOT EXISTS idx_gov_decisions_verdict ON governance_decisions(verdict)",
        "CREATE INDEX IF NOT EXISTS idx_gov_decisions_initiator ON governance_decisions(initiator_id)",
    ],
)

# ===================================================================
# Table 7: did_registry  (identity/DID)
# ===================================================================

DID_REGISTRY_TABLE = OltpTable(
    name="did_registry",
    ddl_postgres="""CREATE TABLE IF NOT EXISTS did_registry (
    did VARCHAR(256) PRIMARY KEY,
    public_key VARCHAR(1024) NOT NULL,
    controller VARCHAR(256),
    verification_method JSONB DEFAULT '{}',
    service_endpoints JSONB DEFAULT '[]',
    attributes JSONB DEFAULT '{}',
    is_revoked BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
)""",
    ddl_sqlite="""CREATE TABLE IF NOT EXISTS did_registry (
    did TEXT PRIMARY KEY,
    public_key TEXT NOT NULL,
    controller TEXT,
    verification_method TEXT DEFAULT '{}',
    service_endpoints TEXT DEFAULT '[]',
    attributes TEXT DEFAULT '{}',
    is_revoked INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
)""",
    columns=[
        {"name": "did", "type": "VARCHAR(256)/TEXT", "nullable": False, "pk": True},
        {"name": "public_key", "type": "VARCHAR(1024)/TEXT", "nullable": False},
        {"name": "controller", "type": "VARCHAR(256)/TEXT"},
        {"name": "verification_method", "type": "JSONB/TEXT"},
        {"name": "service_endpoints", "type": "JSONB/TEXT"},
        {"name": "attributes", "type": "JSONB/TEXT"},
        {"name": "is_revoked", "type": "BOOLEAN/INTEGER", "default": False},
        {"name": "created_at", "type": "TIMESTAMPTZ/TEXT"},
        {"name": "updated_at", "type": "TIMESTAMPTZ/TEXT"},
    ],
    indexes=[
        "CREATE INDEX IF NOT EXISTS idx_did_registry_controller ON did_registry(controller)",
    ],
)

# ===================================================================
# Table 8: node_registry  (mesh node registry — replaces JSONL)
# ===================================================================

NODE_REGISTRY_TABLE = OltpTable(
    name="node_registry",
    ddl_postgres="""CREATE TABLE IF NOT EXISTS node_registry (
    node_id VARCHAR(256) PRIMARY KEY,
    node_type VARCHAR(64),
    host VARCHAR(256),
    port_udp INTEGER,
    port_ws INTEGER,
    public_key VARCHAR(1024),
    region VARCHAR(128),
    trust_score FLOAT DEFAULT 0.5,
    is_active BOOLEAN DEFAULT true,
    last_seen TIMESTAMPTZ,
    capabilities JSONB DEFAULT '[]',
    metadata JSONB DEFAULT '{}',
    registered_at TIMESTAMPTZ DEFAULT NOW()
)""",
    ddl_sqlite="""CREATE TABLE IF NOT EXISTS node_registry (
    node_id TEXT PRIMARY KEY,
    node_type TEXT,
    host TEXT,
    port_udp INTEGER,
    port_ws INTEGER,
    public_key TEXT,
    region TEXT,
    trust_score REAL DEFAULT 0.5,
    is_active INTEGER DEFAULT 1,
    last_seen TEXT,
    capabilities TEXT DEFAULT '[]',
    metadata TEXT DEFAULT '{}',
    registered_at TEXT DEFAULT (datetime('now'))
)""",
    columns=[
        {"name": "node_id", "type": "VARCHAR(256)/TEXT", "nullable": False, "pk": True},
        {"name": "node_type", "type": "VARCHAR(64)/TEXT"},
        {"name": "host", "type": "VARCHAR(256)/TEXT"},
        {"name": "port_udp", "type": "INTEGER/INTEGER"},
        {"name": "port_ws", "type": "INTEGER/INTEGER"},
        {"name": "public_key", "type": "VARCHAR(1024)/TEXT"},
        {"name": "region", "type": "VARCHAR(128)/TEXT"},
        {"name": "trust_score", "type": "FLOAT/REAL", "default": 0.5},
        {"name": "is_active", "type": "BOOLEAN/INTEGER", "default": True},
        {"name": "last_seen", "type": "TIMESTAMPTZ/TEXT"},
        {"name": "capabilities", "type": "JSONB/TEXT"},
        {"name": "metadata", "type": "JSONB/TEXT"},
        {"name": "registered_at", "type": "TIMESTAMPTZ/TEXT"},
    ],
    indexes=[
        "CREATE INDEX IF NOT EXISTS idx_node_registry_type ON node_registry(node_type)",
        "CREATE INDEX IF NOT EXISTS idx_node_registry_active ON node_registry(is_active)",
        "CREATE INDEX IF NOT EXISTS idx_node_registry_region ON node_registry(region)",
    ],
)

# ===================================================================
# Table 9: federation_state  (federation peers)
# ===================================================================

FEDERATION_STATE_TABLE = OltpTable(
    name="federation_state",
    ddl_postgres="""CREATE TABLE IF NOT EXISTS federation_state (
    federation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    peer_did VARCHAR(256) NOT NULL,
    peer_url VARCHAR(1024),
    peer_name VARCHAR(256),
    status VARCHAR(64) DEFAULT 'pending',
    trust_level FLOAT DEFAULT 0.3,
    agreement_hash VARCHAR(128),
    capabilities JSONB DEFAULT '[]',
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    last_sync TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'
)""",
    ddl_sqlite="""CREATE TABLE IF NOT EXISTS federation_state (
    federation_id TEXT PRIMARY KEY,
    peer_did TEXT NOT NULL,
    peer_url TEXT,
    peer_name TEXT,
    status TEXT DEFAULT 'pending',
    trust_level REAL DEFAULT 0.3,
    agreement_hash TEXT,
    capabilities TEXT DEFAULT '[]',
    joined_at TEXT DEFAULT (datetime('now')),
    last_sync TEXT,
    metadata TEXT DEFAULT '{}'
)""",
    columns=[
        {"name": "federation_id", "type": "UUID/TEXT", "nullable": False, "pk": True},
        {"name": "peer_did", "type": "VARCHAR(256)/TEXT", "nullable": False},
        {"name": "peer_url", "type": "VARCHAR(1024)/TEXT"},
        {"name": "peer_name", "type": "VARCHAR(256)/TEXT"},
        {"name": "status", "type": "VARCHAR(64)/TEXT", "default": "pending"},
        {"name": "trust_level", "type": "FLOAT/REAL", "default": 0.3},
        {"name": "agreement_hash", "type": "VARCHAR(128)/TEXT"},
        {"name": "capabilities", "type": "JSONB/TEXT"},
        {"name": "joined_at", "type": "TIMESTAMPTZ/TEXT"},
        {"name": "last_sync", "type": "TIMESTAMPTZ/TEXT"},
        {"name": "metadata", "type": "JSONB/TEXT"},
    ],
    indexes=[
        "CREATE INDEX IF NOT EXISTS idx_fed_state_peer_did ON federation_state(peer_did)",
        "CREATE INDEX IF NOT EXISTS idx_fed_state_status ON federation_state(status)",
    ],
)

# ===================================================================
# Table 10: notifications  (replaces in-memory notification controller)
# ===================================================================

NOTIFICATIONS_TABLE = OltpTable(
    name="notifications",
    ddl_postgres="""CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    type VARCHAR(64) NOT NULL,
    severity VARCHAR(32) DEFAULT 'info',
    title VARCHAR(256) NOT NULL,
    message TEXT,
    source VARCHAR(128),
    is_read BOOLEAN DEFAULT false,
    is_dismissed BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
)""",
    ddl_sqlite="""CREATE TABLE IF NOT EXISTS notifications (
    id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES users(id),
    type TEXT NOT NULL,
    severity TEXT DEFAULT 'info',
    title TEXT NOT NULL,
    message TEXT,
    source TEXT,
    is_read INTEGER DEFAULT 0,
    is_dismissed INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
)""",
    columns=[
        {"name": "id", "type": "UUID/TEXT", "nullable": False, "pk": True},
        {"name": "user_id", "type": "UUID/TEXT", "fk": "users(id)"},
        {"name": "type", "type": "VARCHAR(64)/TEXT", "nullable": False},
        {"name": "severity", "type": "VARCHAR(32)/TEXT", "default": "info"},
        {"name": "title", "type": "VARCHAR(256)/TEXT", "nullable": False},
        {"name": "message", "type": "TEXT/TEXT"},
        {"name": "source", "type": "VARCHAR(128)/TEXT"},
        {"name": "is_read", "type": "BOOLEAN/INTEGER", "default": False},
        {"name": "is_dismissed", "type": "BOOLEAN/INTEGER", "default": False},
        {"name": "created_at", "type": "TIMESTAMPTZ/TEXT"},
    ],
    indexes=[
        "CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type)",
        "CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read)",
        "CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at)",
    ],
)


# ===================================================================
# Registry
# ===================================================================

TABLES: Dict[str, OltpTable] = {
    "users": USERS_TABLE,
    "sessions": SESSIONS_TABLE,
    "credit_accounts": CREDIT_ACCOUNTS_TABLE,
    "credit_transactions": CREDIT_TRANSACTIONS_TABLE,
    "governance_state": GOVERNANCE_STATE_TABLE,
    "governance_decisions": GOVERNANCE_DECISIONS_TABLE,
    "did_registry": DID_REGISTRY_TABLE,
    "node_registry": NODE_REGISTRY_TABLE,
    "federation_state": FEDERATION_STATE_TABLE,
    "notifications": NOTIFICATIONS_TABLE,
}

ALL_MODELS: List[OltpTable] = list(TABLES.values())
