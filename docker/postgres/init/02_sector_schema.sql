-- ASIMNEXUS Sector Module PostgreSQL Schema
-- ============================================
-- This is the PostgreSQL-specific initialization script for sector tables.
-- Used by docker/postgres when starting fresh. For existing databases,
-- use Alembic migrations (migrations/versions/002_sector_tables.py).

BEGIN;

-- ─── Hospital Sector ────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS sector_hospitals (
    hospital_id      VARCHAR(64) PRIMARY KEY,
    name             VARCHAR(256) NOT NULL,
    address          TEXT,
    phone            VARCHAR(32),
    email            VARCHAR(256),
    department_count INTEGER DEFAULT 0,
    bed_count        INTEGER DEFAULT 0,
    staff_count      INTEGER DEFAULT 0,
    status           VARCHAR(32) DEFAULT 'active',
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sector_patients (
    patient_id   VARCHAR(64) PRIMARY KEY,
    hospital_id  VARCHAR(64) NOT NULL REFERENCES sector_hospitals(hospital_id) ON DELETE CASCADE,
    name         VARCHAR(256) NOT NULL,
    age          INTEGER,
    gender       VARCHAR(16),
    blood_type   VARCHAR(8),
    diagnosis    TEXT,
    department   VARCHAR(64),
    status       VARCHAR(32) DEFAULT 'admitted',
    notes        TEXT,
    admitted_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    discharged_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_patients_hospital ON sector_patients(hospital_id);
CREATE INDEX IF NOT EXISTS idx_patients_status ON sector_patients(status);

-- ─── Hotel Sector ───────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS sector_hotel_rooms (
    room_id         VARCHAR(64) PRIMARY KEY,
    room_number     VARCHAR(16) NOT NULL,
    room_type       VARCHAR(64),
    floor           INTEGER,
    capacity        INTEGER DEFAULT 2,
    price_per_night NUMERIC(12,2) DEFAULT 0.0,
    amenities       TEXT,
    status          VARCHAR(32) DEFAULT 'available',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_rooms_status ON sector_hotel_rooms(status);

CREATE TABLE IF NOT EXISTS sector_hotel_bookings (
    booking_id       VARCHAR(64) PRIMARY KEY,
    room_id          VARCHAR(64) NOT NULL REFERENCES sector_hotel_rooms(room_id) ON DELETE CASCADE,
    guest_name       VARCHAR(256) NOT NULL,
    guest_email      VARCHAR(256),
    guest_phone      VARCHAR(32),
    check_in         DATE NOT NULL,
    check_out        DATE NOT NULL,
    total_amount     NUMERIC(12,2) DEFAULT 0.0,
    special_requests TEXT,
    status           VARCHAR(32) DEFAULT 'confirmed',
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    checked_in_at    TIMESTAMP,
    checked_out_at   TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_bookings_room ON sector_hotel_bookings(room_id);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON sector_hotel_bookings(status);

-- ─── Education Sector ───────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS sector_students (
    student_id     VARCHAR(64) PRIMARY KEY,
    name           VARCHAR(256) NOT NULL,
    email          VARCHAR(256),
    phone          VARCHAR(32),
    date_of_birth  DATE,
    address        TEXT,
    program        VARCHAR(128),
    gpa            NUMERIC(4,2) DEFAULT 0.0,
    credits_earned INTEGER DEFAULT 0,
    status         VARCHAR(32) DEFAULT 'active',
    enrolled_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    graduated_at   TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_students_program ON sector_students(program);
CREATE INDEX IF NOT EXISTS idx_students_status ON sector_students(status);

CREATE TABLE IF NOT EXISTS sector_courses (
    course_id    VARCHAR(64) PRIMARY KEY,
    name         VARCHAR(256) NOT NULL,
    code         VARCHAR(32),
    description  TEXT,
    level        VARCHAR(32),
    credits      INTEGER DEFAULT 3,
    department   VARCHAR(64),
    instructor   VARCHAR(256),
    capacity     INTEGER DEFAULT 50,
    status       VARCHAR(32) DEFAULT 'active',
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sector_enrollments (
    id           VARCHAR(64) PRIMARY KEY,
    student_id   VARCHAR(64) NOT NULL REFERENCES sector_students(student_id) ON DELETE CASCADE,
    course_id    VARCHAR(64) NOT NULL REFERENCES sector_courses(course_id) ON DELETE CASCADE,
    status       VARCHAR(32) DEFAULT 'enrolled',
    grade        VARCHAR(4),
    enrolled_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, course_id)
);

-- ─── Banking Sector ─────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS sector_bank_accounts (
    account_id    VARCHAR(64) PRIMARY KEY,
    owner_name    VARCHAR(256) NOT NULL,
    owner_id      VARCHAR(64),
    account_type  VARCHAR(32) DEFAULT 'savings',
    currency      VARCHAR(8) DEFAULT 'NRS',
    balance       NUMERIC(16,2) DEFAULT 0.0,
    kyc_verified  BOOLEAN DEFAULT FALSE,
    status        VARCHAR(32) DEFAULT 'active',
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_bank_accounts_owner ON sector_bank_accounts(owner_id);
CREATE INDEX IF NOT EXISTS idx_bank_accounts_status ON sector_bank_accounts(status);

CREATE TABLE IF NOT EXISTS sector_transactions (
    transaction_id   VARCHAR(64) PRIMARY KEY,
    account_id       VARCHAR(64) NOT NULL REFERENCES sector_bank_accounts(account_id) ON DELETE CASCADE,
    transaction_type VARCHAR(32) NOT NULL,
    amount           NUMERIC(16,2) NOT NULL,
    balance_before   NUMERIC(16,2),
    balance_after    NUMERIC(16,2),
    description      TEXT,
    reference_account VARCHAR(64),
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_transactions_account ON sector_transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_created ON sector_transactions(created_at);

-- ─── Global Agent Tables ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS global_regions (
    region_id      VARCHAR(64) PRIMARY KEY,
    name           VARCHAR(256) NOT NULL,
    endpoint       VARCHAR(512),
    region_type    VARCHAR(32) DEFAULT 'auto',
    status         VARCHAR(32) DEFAULT 'active',
    agent_count    INTEGER DEFAULT 0,
    deployed       BOOLEAN DEFAULT FALSE,
    registered_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS global_agents (
    agent_id        VARCHAR(64) PRIMARY KEY,
    agent_type      VARCHAR(64) NOT NULL,
    region_id       VARCHAR(64) NOT NULL,
    capabilities    TEXT,
    status          VARCHAR(32) DEFAULT 'active',
    tasks_completed INTEGER DEFAULT 0,
    registered_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_heartbeat  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_global_agents_region ON global_agents(region_id);
CREATE INDEX IF NOT EXISTS idx_global_agents_status ON global_agents(status);

-- ─── Security Audit Log ─────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS security_audit_log (
    id             VARCHAR(64) PRIMARY KEY,
    action         VARCHAR(128) NOT NULL,
    resource_type  VARCHAR(64),
    resource_id    VARCHAR(128),
    actor_id       VARCHAR(64),
    allowed        BOOLEAN,
    risk_score     NUMERIC(4,2),
    details        TEXT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_audit_action ON security_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_created ON security_audit_log(created_at);

COMMIT;
