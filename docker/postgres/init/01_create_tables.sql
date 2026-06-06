-- =============================================================================
-- ASIMNEXUS PostgreSQL — DDL for OLTP Tables
-- =============================================================================
-- Auto-generated from storage/schemas/oltp_models.py
-- These tables store transactional/relational data: users, sessions, credits,
-- governance state, DID registry, mesh nodes, federation, notifications.
-- =============================================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- Table 1: users — User accounts and profiles
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
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
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- =============================================================================
-- Table 2: sessions — User authentication sessions
-- =============================================================================
CREATE TABLE IF NOT EXISTS sessions (
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
);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);

-- =============================================================================
-- Table 3: credit_accounts — Economy/credit system
-- =============================================================================
CREATE TABLE IF NOT EXISTS credit_accounts (
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
);

CREATE INDEX IF NOT EXISTS idx_credit_accounts_user_id ON credit_accounts(user_id);
CREATE INDEX IF NOT EXISTS idx_credit_accounts_type ON credit_accounts(account_type);

-- =============================================================================
-- Table 4: credit_transactions — Credit transaction ledger
-- =============================================================================
CREATE TABLE IF NOT EXISTS credit_transactions (
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
);

CREATE INDEX IF NOT EXISTS idx_credit_tx_account_id ON credit_transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_credit_tx_type ON credit_transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_credit_tx_status ON credit_transactions(status);
CREATE INDEX IF NOT EXISTS idx_credit_tx_created ON credit_transactions(created_at);

-- =============================================================================
-- Table 5: governance_state — Governance blockchain state
-- =============================================================================
CREATE TABLE IF NOT EXISTS governance_state (
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
);

CREATE INDEX IF NOT EXISTS idx_gov_state_block ON governance_state(block_number);
CREATE INDEX IF NOT EXISTS idx_gov_state_type ON governance_state(governance_type);
CREATE INDEX IF NOT EXISTS idx_gov_state_status ON governance_state(status);
CREATE INDEX IF NOT EXISTS idx_gov_state_proposal ON governance_state(proposal_id);

-- =============================================================================
-- Table 6: governance_decisions — Audit trail for governance actions
-- =============================================================================
CREATE TABLE IF NOT EXISTS governance_decisions (
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
);

CREATE INDEX IF NOT EXISTS idx_gov_decisions_type ON governance_decisions(decision_type);
CREATE INDEX IF NOT EXISTS idx_gov_decisions_verdict ON governance_decisions(verdict);
CREATE INDEX IF NOT EXISTS idx_gov_decisions_initiator ON governance_decisions(initiator_id);

-- =============================================================================
-- Table 7: did_registry — Decentralized Identifier registry
-- =============================================================================
CREATE TABLE IF NOT EXISTS did_registry (
    did VARCHAR(256) PRIMARY KEY,
    public_key VARCHAR(1024) NOT NULL,
    controller VARCHAR(256),
    verification_method JSONB DEFAULT '{}',
    service_endpoints JSONB DEFAULT '[]',
    attributes JSONB DEFAULT '{}',
    is_revoked BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_did_registry_controller ON did_registry(controller);

-- =============================================================================
-- Table 8: node_registry — P2P mesh node registry
-- =============================================================================
CREATE TABLE IF NOT EXISTS node_registry (
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
);

CREATE INDEX IF NOT EXISTS idx_node_registry_type ON node_registry(node_type);
CREATE INDEX IF NOT EXISTS idx_node_registry_active ON node_registry(is_active);
CREATE INDEX IF NOT EXISTS idx_node_registry_region ON node_registry(region);

-- =============================================================================
-- Table 9: federation_state — Cross-instance federation peers
-- =============================================================================
CREATE TABLE IF NOT EXISTS federation_state (
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
);

CREATE INDEX IF NOT EXISTS idx_fed_state_peer_did ON federation_state(peer_did);
CREATE INDEX IF NOT EXISTS idx_fed_state_status ON federation_state(status);

-- =============================================================================
-- Table 10: notifications — User notification system
-- =============================================================================
CREATE TABLE IF NOT EXISTS notifications (
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
);

CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at);

-- =============================================================================
-- Triggers: auto-update `updated_at` columns
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_credit_accounts_updated_at
    BEFORE UPDATE ON credit_accounts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_did_registry_updated_at
    BEFORE UPDATE ON did_registry
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
