#!/usr/bin/env python3
"""
AsimNexus Demo Dataset Seed
============================
Populates the system with comprehensive demo data for all modules.

Usage:
    python scripts/seed_demo_data.py          # Seed all demo data
    python scripts/seed_demo_data.py --users  # Seed users only
    python scripts/seed_demo_data.py --mesh   # Seed mesh peers/ops only
    python scripts/seed_demo_data.py --nepal  # Seed Nepal demo data only
    python scripts/seed_demo_data.py --finance # Seed finance data only

Output: Pure ASCII, Windows CP1252 compatible.
"""

import sys
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import json
import logging
import sqlite3
import secrets
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("SeedDemoData")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "asim.db"

SEP = "=" * 72

# ─── Demo Users ───────────────────────────────────────────────────────────────

DEMO_USERS = [
    {
        "user_id": "demo_nepal_admin",
        "email": "admin@asimnexus.np",
        "display_name": "Nepal Admin",
        "country": "NP",
        "role": "admin",
    },
    {
        "user_id": "demo_teacher_kathmandu",
        "email": "teacher@school.edu.np",
        "display_name": "Sita Sharma",
        "country": "NP",
        "role": "teacher",
    },
    {
        "user_id": "demo_doctor_pokhara",
        "email": "doctor@health.np",
        "display_name": "Ram Pandey",
        "country": "NP",
        "role": "doctor",
    },
    {
        "user_id": "demo_farmer_chitwan",
        "email": "farmer@agri.np",
        "display_name": "Hari Bahadur",
        "country": "NP",
        "role": "farmer",
    },
    {
        "user_id": "demo_entrepreneur",
        "email": "founder@startup.np",
        "display_name": "Anjali Gurung",
        "country": "NP",
        "role": "entrepreneur",
    },
    {
        "user_id": "demo_global_dev",
        "email": "dev@example.com",
        "display_name": "Alex Chen",
        "country": "US",
        "role": "developer",
    },
]

# ─── Demo Mesh Peers ──────────────────────────────────────────────────────────

DEMO_PEERS = [
    {
        "node_id": "node-kathmandu-01",
        "hostname": "10.0.1.10",
        "port": 9100,
        "trust_level": 0.95,
        "latency_ms": 12.0,
        "region": "Kathmandu",
    },
    {
        "node_id": "node-pokhara-01",
        "hostname": "10.0.2.10",
        "port": 9101,
        "trust_level": 0.85,
        "latency_ms": 28.0,
        "region": "Pokhara",
    },
    {
        "node_id": "node-chitwan-01",
        "hostname": "10.0.3.10",
        "port": 9102,
        "trust_level": 0.70,
        "latency_ms": 45.0,
        "region": "Chitwan",
    },
    {
        "node_id": "node-lumbini-01",
        "hostname": "10.0.4.10",
        "port": 9103,
        "trust_level": 0.65,
        "latency_ms": 52.0,
        "region": "Lumbini",
    },
    {
        "node_id": "node-remote-01",
        "hostname": "10.0.9.99",
        "port": 9199,
        "trust_level": 0.30,
        "latency_ms": 180.0,
        "region": "Remote Village",
    },
]

# ─── Demo CRDT Operations ─────────────────────────────────────────────────────

DEMO_OPERATIONS = [
    {"crdt_id": "doc:nepal-guide", "operation": "create",
     "key": "title", "value": "Nepal Travel Guide"},
    {"crdt_id": "doc:nepal-guide", "operation": "update",
     "key": "content", "value": "Kathmandu Valley cultural heritage sites..."},
    {"crdt_id": "doc:nepal-guide", "operation": "update",
     "key": "author", "value": "demo_teacher_kathmandu"},
    {"crdt_id": "doc:health-protocol", "operation": "create",
     "key": "title", "value": "Rural Health Protocol"},
    {"crdt_id": "doc:health-protocol", "operation": "update",
     "key": "region", "value": "Gandaki Province"},
    {"crdt_id": "doc:agri-calendar", "operation": "create",
     "key": "title", "value": "Nepali Agricultural Calendar 2082"},
    {"crdt_id": "doc:agri-calendar", "operation": "update",
     "key": "data", "value": "Rice: June-July, Wheat: Nov-Dec, Maize: Mar-Apr"},
    {"crdt_id": "config:mesh-routing", "operation": "create",
     "key": "strategy", "value": "lowest_latency"},
    {"crdt_id": "config:sync-policy", "operation": "update",
     "key": "interval", "value": "300"},
    {"crdt_id": "doc:startup-guide", "operation": "create",
     "key": "title", "value": "Nepal Startup Ecosystem Guide"},
]

# ─── Demo Financial Data ──────────────────────────────────────────────────────

DEMO_WALLETS = [
    {"user_id": "demo_nepal_admin", "currency": "NPR", "balance": 50000.0},
    {"user_id": "demo_nepal_admin", "currency": "USD", "balance": 500.0},
    {"user_id": "demo_teacher_kathmandu", "currency": "NPR", "balance": 15000.0},
    {"user_id": "demo_doctor_pokhara", "currency": "NPR", "balance": 35000.0},
    {"user_id": "demo_farmer_chitwan", "currency": "NPR", "balance": 8000.0},
    {"user_id": "demo_entrepreneur", "currency": "NPR", "balance": 100000.0},
    {"user_id": "demo_entrepreneur", "currency": "USD", "balance": 2000.0},
]

DEMO_TRANSACTIONS = [
    {"from_id": "demo_entrepreneur", "to_id": "demo_farmer_chitwan",
     "amount": 5000.0, "currency": "NPR", "note": "Seed funding for cooperative"},
    {"from_id": "demo_nepal_admin", "to_id": "demo_teacher_kathmandu",
     "amount": 2500.0, "currency": "NPR", "note": "Grant for digital classroom"},
    {"from_id": "demo_doctor_pokhara", "to_id": "demo_farmer_chitwan",
     "amount": 1000.0, "currency": "NPR", "note": "Telemedicine equipment"},
]


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _get_db() -> sqlite3.Connection:
    """Get database connection with row factory."""
    db_path = str(DB_PATH)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def seed_users() -> int:
    """Seed demo users into the database. Returns count."""
    count = 0
    try:
        conn = _get_db()
        for user in DEMO_USERS:
            token = secrets.token_hex(32)
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                """INSERT OR IGNORE INTO users
                   (user_id, email, display_name, country, role, token, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (user["user_id"], user["email"], user["display_name"],
                 user["country"], user["role"], token, now),
            )
            if conn.total_changes:
                count += 1
        conn.commit()
        conn.close()
        logger.info("Seeded %d user(s)", count)
    except Exception as e:
        logger.warning("Users seed (non-fatal): %s", e)
    return count


def seed_mesh_peers() -> int:
    """Seed demo mesh peer data via the sync engine. Returns count."""
    count = 0
    try:
        from mesh.offline_sync_engine import SyncPeer, SyncPriority, get_offline_sync_engine
        engine = get_offline_sync_engine()
        for peer_data in DEMO_PEERS:
            peer = SyncPeer(
                node_id=peer_data["node_id"],
                hostname=peer_data["hostname"],
                port=peer_data["port"],
                trust_level=peer_data["trust_level"],
                latency_ms=peer_data["latency_ms"],
            )
            # Enqueue peer registration as a sync operation
            engine.enqueue_operation(
                crdt_id=f"peer:{peer_data['node_id']}",
                operation="register",
                key="node_info",
                value=peer_data,
                priority=SyncPriority.HIGH,
            )
            count += 1
        engine.sync_now()
        logger.info("Registered %d mesh peer(s)", count)
    except Exception as e:
        logger.warning("Mesh peers seed (non-fatal): %s", e)
    return count


def seed_sync_operations() -> int:
    """Seed demo CRDT operations via the sync engine. Returns count."""
    count = 0
    try:
        from mesh.offline_sync_engine import get_offline_sync_engine
        engine = get_offline_sync_engine()
        for op in DEMO_OPERATIONS:
            engine.enqueue_operation(
                crdt_id=op["crdt_id"],
                operation=op["operation"],
                key=op["key"],
                value=op["value"],
            )
            count += 1
        logger.info("Seeded %d sync operation(s)", count)
    except Exception as e:
        logger.warning("Sync ops seed (non-fatal): %s", e)
    return count


def seed_wallets() -> int:
    """Seed demo wallet data. Returns count."""
    count = 0
    try:
        conn = _get_db()
        for wallet in DEMO_WALLETS:
            conn.execute(
                """INSERT OR IGNORE INTO wallets
                   (user_id, currency, balance) VALUES (?, ?, ?)""",
                (wallet["user_id"], wallet["currency"], wallet["balance"]),
            )
            if conn.total_changes:
                count += 1
        conn.commit()
        conn.close()
        logger.info("Seeded %d wallet(s)", count)
    except Exception as e:
        logger.warning("Wallets seed (non-fatal): %s", e)
    return count


def seed_transactions() -> int:
    """Seed demo transactions. Returns count."""
    count = 0
    try:
        conn = _get_db()
        now_ts = datetime.now(timezone.utc).timestamp()
        for tx in DEMO_TRANSACTIONS:
            tx_id = f"demo-tx-{count + 1:03d}"
            conn.execute(
                """INSERT OR IGNORE INTO transactions
                   (tx_id, from_user, to_user, amount, currency, note, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (tx_id, tx["from_id"], tx["to_id"], tx["amount"],
                 tx["currency"], tx["note"], now_ts),
            )
            if conn.total_changes:
                count += 1
            now_ts += 1.0  # increment timestamp
        conn.commit()
        conn.close()
        logger.info("Seeded %d transaction(s)", count)
    except Exception as e:
        logger.warning("Transactions seed (non-fatal): %s", e)
    return count


def seed_nepal_data() -> Dict:
    """Seed Nepal-specific demo data and verify modules. Returns results."""
    results = {}
    try:
        from core.nepal import (
            get_banking_status,
            get_telecom_status,
            get_government_status,
            get_language_status,
            get_cultural_status,
        )
        results["banking"] = get_banking_status()["status"]
        results["telecom"] = get_telecom_status()["status"]
        results["government"] = get_government_status()["status"]
        results["language"] = get_language_status()["status"]
        results["culture"] = get_cultural_status()["status"]

        # Process demo payments
        from core.nepal.banking_integrations import process_payment
        payment = process_payment("esewa", 1500.0, "NPR",
                                  metadata={"purpose": "demo_seed"})
        results["payment"] = "ok" if payment["success"] else "failed"

        # Verify identity
        from core.nepal.government_integrations import verify_identity
        identity = verify_identity("citizenship", "NP-XX-12345678", "basic")
        results["identity"] = "ok" if identity["verified"] else "failed"

        logger.info("Nepal module health: %s", results)
    except Exception as e:
        logger.warning("Nepal data seed (non-fatal): %s", e)
        results["error"] = str(e)[:60]
    return results


# ─── Main ─────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Seed demo dataset")
    parser.add_argument("--users", action="store_true", help="Seed users only")
    parser.add_argument("--mesh", action="store_true", help="Seed mesh data only")
    parser.add_argument("--nepal", action="store_true", help="Seed Nepal data only")
    parser.add_argument("--finance", action="store_true", help="Seed finance data only")
    args = parser.parse_args()

    print(SEP)
    print("  AsimNexus Demo Dataset Seed")
    print(SEP)

    all_modules = not (args.users or args.mesh or args.nepal or args.finance)

    start = time.time()

    if all_modules or args.users:
        print("\n[1/5] Seeding demo users...")
        u = seed_users()
        print(f"  [OK] {u} user(s) seeded")

    if all_modules or args.mesh:
        print("\n[2/5] Seeding mesh data...")
        p = seed_mesh_peers()
        o = seed_sync_operations()
        print(f"  [OK] {p} peer(s) registered")
        print(f"  [OK] {o} operation(s) queued")

    if all_modules or args.nepal:
        print("\n[3/5] Seeding Nepal module data...")
        nr = seed_nepal_data()
        if "error" in nr:
            print(f"  [--] Nepal modules: {nr['error']}")
        else:
            print(f"  [OK] Banking: {nr.get('banking', '?')}")
            print(f"  [OK] Telecom: {nr.get('telecom', '?')}")
            print(f"  [OK] Government: {nr.get('government', '?')}")
            print(f"  [OK] Language: {nr.get('language', '?')}")
            print(f"  [OK] Culture: {nr.get('culture', '?')}")
            print(f"  [OK] Demo payment: {nr.get('payment', '?')}")
            print(f"  [OK] Demo identity: {nr.get('identity', '?')}")

    if all_modules or args.finance:
        print("\n[4/5] Seeding financial data...")
        w = seed_wallets()
        t = seed_transactions()
        print(f"  [OK] {w} wallet(s) seeded")
        print(f"  [OK] {t} transaction(s) seeded")

    elapsed = time.time() - start
    print(f"\n{SEP}")
    print(f"  [OK] Seeding complete in {elapsed:.2f}s")
    print(f"  [->] Seed script: scripts/seed_demo_data.py")
    print(f"  [->] Database: data/asim.db")
    print(SEP)


if __name__ == "__main__":
    main()
