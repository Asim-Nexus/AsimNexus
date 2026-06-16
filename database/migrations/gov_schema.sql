-- AsimNexus Government Database Schema
-- PostgreSQL migration for government (51%) sector

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Citizens table
CREATE TABLE IF NOT EXISTS citizens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    citizen_id VARCHAR(50) UNIQUE NOT NULL,
    district VARCHAR(50),
    birth_year INTEGER,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Tax records
CREATE TABLE IF NOT EXISTS tax_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    citizen_id VARCHAR(50) REFERENCES citizens(citizen_id),
    year INTEGER NOT NULL,
    income DECIMAL(15, 2) NOT NULL,
    tax_paid DECIMAL(15, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    filed_at TIMESTAMP DEFAULT NOW(),
    verified_at TIMESTAMP,
    UNIQUE(citizen_id, year)
);

-- Tax slabs (Nepal tax rates)
CREATE TABLE IF NOT EXISTS tax_slabs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slab_name VARCHAR(100),
    min_income DECIMAL(15, 2),
    max_income DECIMAL(15, 2),
    rate DECIMAL(5, 2),
    year INTEGER DEFAULT 2081
);

-- Government proposals
CREATE TABLE IF NOT EXISTS gov_proposals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    proposal_id VARCHAR(100) UNIQUE,
    title TEXT,
    description TEXT,
    sector VARCHAR(20),
    proposer VARCHAR(100),
    threshold DECIMAL(5, 2) DEFAULT 0.51,
    created_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active'
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_tax_records_year ON tax_records(year);
CREATE INDEX IF NOT EXISTS idx_tax_records_citizen ON tax_records(citizen_id);