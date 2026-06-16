-- AsimNexus Company Database Schema
-- PostgreSQL migration for enterprise (49%) sector

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Companies table
CREATE TABLE IF NOT EXISTS companies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name VARCHAR(200) NOT NULL,
    registration_number VARCHAR(100) UNIQUE,
    sector VARCHAR(50),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Employees
CREATE TABLE IF NOT EXISTS employees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id),
    employee_id VARCHAR(50),
    position VARCHAR(100),
    department VARCHAR(100),
    salary DECIMAL(15, 2),
    hired_date TIMESTAMP DEFAULT NOW()
);

-- Financial transactions
CREATE TABLE IF NOT EXISTS transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_id UUID REFERENCES companies(id),
    amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'NPR',
    method VARCHAR(50),
    transaction_id VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'completed'
);

-- Company proposals
CREATE TABLE IF NOT EXISTS company_proposals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    proposal_id VARCHAR(100) UNIQUE,
    title TEXT,
    description TEXT,
    sector VARCHAR(20),
    proposer VARCHAR(100),
    threshold DECIMAL(5, 2) DEFAULT 0.33,
    created_at TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'active'
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_employees_company ON employees(company_id);
CREATE INDEX IF NOT EXISTS idx_transactions_company ON transactions(company_id);