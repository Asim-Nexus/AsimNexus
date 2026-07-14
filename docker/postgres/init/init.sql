-- AsimNexus PostgreSQL Initialization Script
-- =============================================
-- Runs on first database creation to set up schemas, extensions, and base tables.

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Schema: asimnexus (main application data) ──────────────────────────────
CREATE SCHEMA IF NOT EXISTS asimnexus;
SET search_path TO asimnexus, public;

-- Users & Authentication
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(128) UNIQUE NOT NULL,
    email VARCHAR(256) UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'citizen',
    country VARCHAR(4) DEFAULT 'NP',
    locale VARCHAR(10) DEFAULT 'ne-NP',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(256) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Mesh Network
CREATE TABLE IF NOT EXISTS mesh_nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    node_id VARCHAR(128) UNIQUE NOT NULL,
    node_type VARCHAR(32) NOT NULL DEFAULT 'peer',
    address VARCHAR(256),
    port INTEGER,
    public_key TEXT,
    trust_score FLOAT DEFAULT 0.5,
    is_active BOOLEAN DEFAULT TRUE,
    last_seen TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mesh_operations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    operation_type VARCHAR(64) NOT NULL,
    entity_type VARCHAR(64),
    entity_id VARCHAR(128),
    payload JSONB,
    status VARCHAR(32) DEFAULT 'pending',
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

-- Federation
CREATE TABLE IF NOT EXISTS federation_peers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    peer_id VARCHAR(128) UNIQUE NOT NULL,
    peer_url VARCHAR(512),
    jurisdiction VARCHAR(4),
    consent_granted BOOLEAN DEFAULT FALSE,
    consent_expires_at TIMESTAMPTZ,
    trust_level FLOAT DEFAULT 0.0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Governance & Audit
CREATE TABLE IF NOT EXISTS governance_audit (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action_type VARCHAR(64) NOT NULL,
    actor_id VARCHAR(128),
    target_type VARCHAR(64),
    target_id VARCHAR(128),
    details JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS constitution_anchors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    anchor_hash VARCHAR(128) UNIQUE NOT NULL,
    document_type VARCHAR(64) NOT NULL,
    version VARCHAR(16),
    content_hash VARCHAR(128),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Economy & Contracts
CREATE TABLE IF NOT EXISTS agent_contracts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contract_type VARCHAR(64) NOT NULL,
    parties JSONB NOT NULL,
    terms JSONB,
    status VARCHAR(32) DEFAULT 'draft',
    jurisdiction VARCHAR(4),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Nepal-specific tables
CREATE TABLE IF NOT EXISTS nepal_citizens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    citizen_id VARCHAR(64) UNIQUE NOT NULL,
    full_name VARCHAR(256),
    date_of_birth DATE,
    nationality VARCHAR(4) DEFAULT 'NP',
    document_type VARCHAR(32),
    document_number VARCHAR(128),
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS nepal_tax_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    citizen_id VARCHAR(64) NOT NULL,
    tax_year INTEGER NOT NULL,
    income DECIMAL(15,2),
    tax_amount DECIMAL(15,2),
    currency VARCHAR(4) DEFAULT 'NPR',
    filing_status VARCHAR(32) DEFAULT 'pending',
    filed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_mesh_nodes_node_id ON mesh_nodes(node_id);
CREATE INDEX IF NOT EXISTS idx_mesh_operations_status ON mesh_operations(status);
CREATE INDEX IF NOT EXISTS idx_mesh_operations_created ON mesh_operations(created_at);
CREATE INDEX IF NOT EXISTS idx_federation_peers_peer_id ON federation_peers(peer_id);
CREATE INDEX IF NOT EXISTS idx_governance_audit_created ON governance_audit(created_at);
CREATE INDEX IF NOT EXISTS idx_nepal_citizens_citizen_id ON nepal_citizens(citizen_id);
CREATE INDEX IF NOT EXISTS idx_nepal_tax_records_citizen ON nepal_tax_records(citizen_id);
