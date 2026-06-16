-- AsimNexus User Database Schema
-- PostgreSQL migration for citizen (Local-First) sector

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- User profiles
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200),
    email VARCHAR(200),
    phone VARCHAR(20),
    preferences JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Digital twins
CREATE TABLE IF NOT EXISTS digital_twins (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100) REFERENCES user_profiles(user_id),
    twin_data JSONB,
    last_sync TIMESTAMP,
    sync_hash VARCHAR(64),
    created_at TIMESTAMP DEFAULT NOW()
);

-- User proposals (lower threshold)
CREATE TABLE IF NOT EXISTS user_proposals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    proposal_id VARCHAR(100) UNIQUE,
    title TEXT,
    description TEXT,
    user_id VARCHAR(100) REFERENCES user_profiles(user_id),
    sector VARCHAR(20) DEFAULT 'user',
    threshold DECIMAL(5, 2) DEFAULT 0.33,
    created_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active'
);

-- Grievances
CREATE TABLE IF NOT EXISTS grievances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    grievance_id VARCHAR(100) UNIQUE,
    user_id VARCHAR(100) REFERENCES user_profiles(user_id),
    category VARCHAR(50),
    description TEXT,
    status VARCHAR(20) DEFAULT 'submitted',
    target_agency VARCHAR(200),
    submitted_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_user_profiles_user ON user_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_digital_twins_user ON digital_twins(user_id);
CREATE INDEX IF NOT EXISTS idx_grievances_user ON grievances(user_id);