--
-- ASIMNEXUS Database Schema
-- PostgreSQL Schema for Digital Twin, Users, and System Logs
-- 
-- Tables:
--   - users: User accounts and authentication
--   - digital_twins: User digital twin profiles
--   - twin_memories: Digital twin memory/history
--   - system_logs: System activity logs
--   - api_usage: API key usage tracking
--   - mesh_nodes: P2P network nodes
--   - blockchain_dids: Decentralized identifiers
--   - quantum_jobs: Quantum computing jobs
--

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. USERS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    username VARCHAR(100) UNIQUE,
    full_name VARCHAR(255),
    phone VARCHAR(50),
    
    -- Profile
    avatar_url TEXT,
    bio TEXT,
    location VARCHAR(255),
    timezone VARCHAR(50) DEFAULT 'UTC',
    language VARCHAR(10) DEFAULT 'en',
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    role VARCHAR(50) DEFAULT 'user', -- user, admin, founder
    
    -- Security
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret VARCHAR(255),
    last_login_at TIMESTAMP,
    login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);

-- ============================================
-- 2. DIGITAL TWINS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS digital_twins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Twin Identity
    twin_name VARCHAR(255) NOT NULL,
    twin_type VARCHAR(50) DEFAULT 'personal', -- personal, professional, agent
    
    -- Birth/Death tracking
    birth_date DATE,
    birth_place VARCHAR(255),
    death_date DATE,
    
    -- Personality (JSON for flexibility)
    personality_traits JSONB DEFAULT '{}',
    values JSONB DEFAULT '{}',
    skills JSONB DEFAULT '[]',
    interests JSONB DEFAULT '[]',
    
    -- Physical attributes
    height_cm INTEGER,
    weight_kg DECIMAL(5,2),
    blood_type VARCHAR(5),
    medical_conditions JSONB DEFAULT '[]',
    allergies JSONB DEFAULT '[]',
    
    -- Social
    family_members JSONB DEFAULT '[]',
    social_graph JSONB DEFAULT '{}',
    
    -- Status
    life_stage VARCHAR(50) DEFAULT 'adult', -- birth, childhood, adolescence, adult, retirement, death
    is_active BOOLEAN DEFAULT TRUE,
    clone_status VARCHAR(50) DEFAULT 'active', -- active, dormant, archived
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_sync_at TIMESTAMP,
    
    -- Blockchain reference
    did_identifier VARCHAR(255),
    blockchain_network VARCHAR(50)
);

-- Indexes
CREATE INDEX idx_twins_user_id ON digital_twins(user_id);
CREATE INDEX idx_twins_life_stage ON digital_twins(life_stage);
CREATE INDEX idx_twins_active ON digital_twins(is_active);
CREATE INDEX idx_twins_did ON digital_twins(did_identifier);

-- ============================================
-- 3. TWIN MEMORIES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS twin_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    twin_id UUID NOT NULL REFERENCES digital_twins(id) ON DELETE CASCADE,
    
    -- Memory content
    memory_type VARCHAR(50) NOT NULL, -- conversation, event, fact, preference, skill
    title VARCHAR(255),
    content TEXT NOT NULL,
    
    -- Context
    context JSONB DEFAULT '{}',
    tags JSONB DEFAULT '[]',
    sentiment VARCHAR(20), -- positive, negative, neutral
    importance_score INTEGER DEFAULT 5, -- 1-10
    
    -- Source
    source_type VARCHAR(50), -- user_input, system_generated, import
    source_id VARCHAR(255),
    
    -- Temporal
    occurred_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    
    -- Status
    is_archived BOOLEAN DEFAULT FALSE,
    is_shared BOOLEAN DEFAULT FALSE,
    access_level VARCHAR(20) DEFAULT 'private' -- private, family, public
);

-- Indexes
CREATE INDEX idx_memories_twin_id ON twin_memories(twin_id);
CREATE INDEX idx_memories_type ON twin_memories(memory_type);
CREATE INDEX idx_memories_occurred ON twin_memories(occurred_at);
CREATE INDEX idx_memories_importance ON twin_memories(importance_score);

-- Full-text search
CREATE INDEX idx_memories_content_search ON twin_memories USING gin(to_tsvector('english', content));

-- ============================================
-- 4. SYSTEM LOGS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS system_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Log details
    log_level VARCHAR(20) NOT NULL, -- DEBUG, INFO, WARNING, ERROR, CRITICAL
    component VARCHAR(100) NOT NULL, -- kernel, network, agi, quantum, blockchain, etc.
    event_type VARCHAR(100) NOT NULL,
    message TEXT NOT NULL,
    
    -- Context
    user_id UUID REFERENCES users(id),
    twin_id UUID REFERENCES digital_twins(id),
    session_id VARCHAR(255),
    request_id VARCHAR(255),
    
    -- Technical details
    stack_trace TEXT,
    metadata JSONB DEFAULT '{}',
    
    -- Source
    ip_address INET,
    user_agent TEXT,
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_logs_level ON system_logs(log_level);
CREATE INDEX idx_logs_component ON system_logs(component);
CREATE INDEX idx_logs_user ON system_logs(user_id);
CREATE INDEX idx_logs_created ON system_logs(created_at);
CREATE INDEX idx_logs_event ON system_logs(event_type);

-- Partition by month for performance (optional, for high volume)
-- CREATE TABLE system_logs_y2024m01 PARTITION OF system_logs
--     FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- ============================================
-- 5. API USAGE TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS api_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- API details
    api_key_id VARCHAR(255) NOT NULL,
    provider VARCHAR(100) NOT NULL, -- openai, anthropic, nvidia_nim, etc.
    model VARCHAR(255),
    endpoint VARCHAR(255),
    
    -- Usage metrics
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    cost_usd DECIMAL(10,6) DEFAULT 0.0,
    latency_ms INTEGER,
    
    -- Context
    user_id UUID REFERENCES users(id),
    twin_id UUID REFERENCES digital_twins(id),
    request_type VARCHAR(100),
    
    -- Status
    status VARCHAR(50) DEFAULT 'success', -- success, error, timeout
    error_message TEXT,
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_api_usage_provider ON api_usage(provider);
CREATE INDEX idx_api_usage_user ON api_usage(user_id);
CREATE INDEX idx_api_usage_created ON api_usage(created_at);
CREATE INDEX idx_api_usage_key ON api_usage(api_key_id);

-- ============================================
-- 6. MESH NODES TABLE (P2P Network)
-- ============================================
CREATE TABLE IF NOT EXISTS mesh_nodes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Node identity
    node_id VARCHAR(255) UNIQUE NOT NULL,
    node_name VARCHAR(255),
    node_type VARCHAR(50) DEFAULT 'peer', -- bootstrap, relay, peer
    
    -- Network details
    ip_address INET,
    port INTEGER,
    public_key TEXT,
    
    -- Status
    is_online BOOLEAN DEFAULT FALSE,
    last_seen_at TIMESTAMP,
    latency_ms INTEGER,
    
    -- Capabilities
    capabilities JSONB DEFAULT '[]',
    region VARCHAR(100),
    country_code VARCHAR(5),
    
    -- Trust
    trust_score DECIMAL(3,2) DEFAULT 0.5, -- 0.00 - 1.00
    reputation INTEGER DEFAULT 0,
    
    -- Metadata
    version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_mesh_nodes_online ON mesh_nodes(is_online);
CREATE INDEX idx_mesh_nodes_region ON mesh_nodes(region);
CREATE INDEX idx_mesh_nodes_trust ON mesh_nodes(trust_score);

-- ============================================
-- 7. BLOCKCHAIN DIDs TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS blockchain_dids (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    twin_id UUID REFERENCES digital_twins(id),
    
    -- DID details
    did_identifier VARCHAR(255) UNIQUE NOT NULL,
    did_document JSONB NOT NULL,
    
    -- Blockchain
    network VARCHAR(50) NOT NULL, -- ethereum, polygon, solana
    contract_address VARCHAR(255),
    wallet_address VARCHAR(255),
    
    -- Verification
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP,
    
    -- Credentials
    credentials_count INTEGER DEFAULT 0,
    credentials JSONB DEFAULT '[]',
    
    -- Status
    status VARCHAR(50) DEFAULT 'active', -- active, revoked, expired
    
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_dids_user ON blockchain_dids(user_id);
CREATE INDEX idx_dids_network ON blockchain_dids(network);
CREATE INDEX idx_dids_status ON blockchain_dids(status);

-- ============================================
-- 8. QUANTUM JOBS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS quantum_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    twin_id UUID REFERENCES digital_twins(id),
    
    -- Job details
    job_name VARCHAR(255),
    algorithm VARCHAR(100) NOT NULL, -- grover, shor, vqe, qaoa
    provider VARCHAR(50) NOT NULL, -- ibm, amazon, azure, simulator
    device_id VARCHAR(255),
    
    -- Circuit/Program
    circuit_json JSONB,
    qubits INTEGER,
    shots INTEGER DEFAULT 1024,
    
    -- Status
    status VARCHAR(50) DEFAULT 'pending', -- pending, running, completed, error
    progress INTEGER DEFAULT 0, -- 0-100
    
    -- Results
    result JSONB,
    execution_time_ms INTEGER,
    cost_usd DECIMAL(10,6),
    
    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    
    -- Timestamps
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    expires_at TIMESTAMP
);

-- Indexes
CREATE INDEX idx_quantum_user ON quantum_jobs(user_id);
CREATE INDEX idx_quantum_status ON quantum_jobs(status);
CREATE INDEX idx_quantum_provider ON quantum_jobs(provider);
CREATE INDEX idx_quantum_submitted ON quantum_jobs(submitted_at);

-- ============================================
-- 9. CONVERSATIONS TABLE (AGI Chat)
-- ============================================
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    twin_id UUID REFERENCES digital_twins(id),
    
    -- Conversation details
    title VARCHAR(255),
    context JSONB DEFAULT '{}',
    
    -- Settings
    model_used VARCHAR(100),
    reasoning_mode VARCHAR(50), -- quick, analytical, creative
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    message_count INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    
    -- Message content
    role VARCHAR(50) NOT NULL, -- user, assistant, system
    content TEXT NOT NULL,
    
    -- Metadata
    tokens_used INTEGER,
    model VARCHAR(100),
    thinking_process TEXT,
    
    -- Status
    is_error BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    
    -- Timestamp
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_twin ON conversations(twin_id);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_created ON messages(created_at);

-- ============================================
-- FUNCTIONS AND TRIGGERS
-- ============================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply to tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_twins_updated_at BEFORE UPDATE ON digital_twins
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_nodes_updated_at BEFORE UPDATE ON mesh_nodes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dids_updated_at BEFORE UPDATE ON blockchain_dids
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- VIEWS FOR COMMON QUERIES
-- ============================================

-- Active twins with user info
CREATE OR REPLACE VIEW active_twins_view AS
SELECT 
    dt.*,
    u.email as user_email,
    u.username,
    u.full_name as user_full_name
FROM digital_twins dt
JOIN users u ON dt.user_id = u.id
WHERE dt.is_active = TRUE AND u.is_active = TRUE;

-- API usage summary by user
CREATE OR REPLACE VIEW user_api_usage_summary AS
SELECT 
    user_id,
    provider,
    COUNT(*) as total_requests,
    SUM(total_tokens) as total_tokens,
    SUM(cost_usd) as total_cost,
    AVG(latency_ms) as avg_latency
FROM api_usage
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY user_id, provider;

-- System health summary
CREATE OR REPLACE VIEW system_health_view AS
SELECT 
    log_level,
    component,
    COUNT(*) as error_count,
    MAX(created_at) as last_occurrence
FROM system_logs
WHERE created_at >= CURRENT_DATE - INTERVAL '24 hours'
    AND log_level IN ('ERROR', 'CRITICAL')
GROUP BY log_level, component;

-- ============================================
-- INITIAL DATA
-- ============================================

-- Insert default admin user (password should be hashed properly in production)
INSERT INTO users (email, username, full_name, password_hash, role, is_verified)
VALUES (
    'admin@asimnexus.com',
    'admin',
    'ASIMNEXUS Administrator',
    '$2b$12$placeholder_hash_change_in_production',
    'admin',
    TRUE
)
ON CONFLICT (email) DO NOTHING;

-- ============================================
-- COMMENTS
-- ============================================

COMMENT ON TABLE users IS 'User accounts for ASIMNEXUS';
COMMENT ON TABLE digital_twins IS 'Digital twin profiles for each user';
COMMENT ON TABLE twin_memories IS 'Memory and history storage for digital twins';
COMMENT ON TABLE system_logs IS 'System activity and error logs';
COMMENT ON TABLE api_usage IS 'API key usage tracking for billing';
COMMENT ON TABLE mesh_nodes IS 'P2P network node registry';
COMMENT ON TABLE blockchain_dids IS 'Decentralized identifier records';
COMMENT ON TABLE quantum_jobs IS 'Quantum computing job tracking';

-- ============================================
-- END OF SCHEMA
-- ============================================
