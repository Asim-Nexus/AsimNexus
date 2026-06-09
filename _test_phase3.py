#!/usr/bin/env python3
"""Quick functional test for Phase 3A economy wiring."""
import asyncio
import json
import sys

from core.economy.contract_executor import (
    get_contract_executor, reset_contract_executor, ContractDuration
)
from economy.nexus_credits import (
    get_nexus_credits, reset_nexus_credits, PackageType
)


async def test_contract_executor():
    """Test contract lifecycle with FSM validation."""
    print("=== Test: Contract Executor FSM ===")
    reset_contract_executor()
    ex = get_contract_executor()

    c = await ex.create_contract("job_001", "client_001", "worker_001",
                                  ContractDuration.SHORT,
                                  {"title": "Test", "payment": 500.0, "currency": "NPR"})
    assert c.status == "pending", f"Expected pending, got {c.status}"
    print(f"  PASS: Created contract, status={c.status}")

    ok = await ex.accept_contract(c.id, "worker_001")
    assert ok, "Accept failed"
    assert ex.contracts[c.id].status == "accepted"
    print(f"  PASS: Accepted contract, status={ex.contracts[c.id].status}")

    ok = await ex.start_contract(c.id, "worker_001")
    assert ok, "Start failed"
    assert ex.contracts[c.id].status == "active"
    print(f"  PASS: Started contract, status={ex.contracts[c.id].status}")

    ok = await ex.complete_contract(c.id, "worker_001")
    assert ok, "Complete failed"
    assert ex.contracts[c.id].status == "completed"
    print(f"  PASS: Completed contract, status={ex.contracts[c.id].status}")

    r = await ex.approve_contract(c.id, "client_001")
    assert r["success"], f"Approve failed: {r}"
    print(f"  PASS: Approved contract")

    r = await ex.release_payment(c.id, "client_001")
    assert r["success"], f"Payment failed: {r}"
    assert r["amount"] == 500.0
    print(f"  PASS: Payment released: {r['amount']}")

    assert len(ex.audit_trail) >= 6, f"Expected >=6 audit entries, got {len(ex.audit_trail)}"
    print(f"  PASS: {len(ex.audit_trail)} audit entries created")

    print("  PASS: Full lifecycle complete\n")
    return True


async def test_fsm_invalid_transition():
    """Test that invalid state transitions are blocked."""
    print("=== Test: FSM Invalid Transitions ===")
    reset_contract_executor()
    ex = get_contract_executor()

    c = await ex.create_contract("job_002", "client_002", "worker_002",
                                  ContractDuration.SHORT,
                                  {"title": "Test2", "payment": 300.0, "currency": "NPR"})

    # Can't complete before accepting
    ok = await ex.complete_contract(c.id, "worker_002")
    assert not ok, "Should not be able to complete before accept"
    print("  PASS: Cannot complete before accept")

    # Can't pay before approve
    ok = await ex.accept_contract(c.id, "worker_002")
    ok = await ex.start_contract(c.id, "worker_002")
    ok = await ex.complete_contract(c.id, "worker_002")
    r = await ex.release_payment(c.id, "client_002")
    assert not r["success"], "Should not be able to pay before approve"
    print("  PASS: Cannot pay before approve")

    print("  PASS: FSM blocks invalid transitions\n")
    return True


async def test_nexus_credits():
    """Test Nexus Credits with persistence."""
    print("=== Test: Nexus Credits ===")
    reset_nexus_credits()
    nc = get_nexus_credits()

    credit = await nc.create_credit("user_001", 10000)
    assert credit.credit_id is not None
    assert nc.get_balance("user_001") == 10000
    print(f"  PASS: Credit created, balance={nc.get_balance('user_001')}")

    txn = await nc.purchase_package("user_001", PackageType.FIVE_DAYS)
    assert txn.transaction_id is not None
    assert nc.get_balance("user_001") == 9500  # 10000 - 500
    print(f"  PASS: Package purchased, balance={nc.get_balance('user_001')}")

    reward = await nc.reward_task_completion("agent_001", "task_123", 500)
    assert reward.transaction_id is not None
    assert nc.get_balance("agent_001") == 500
    print(f"  PASS: Task rewarded, agent balance={nc.get_balance('agent_001')}")

    transfer = await nc.transfer_credits("user_001", "agent_001", 200)
    assert transfer.transaction_id is not None
    assert nc.get_balance("user_001") == 9300
    assert nc.get_balance("agent_001") == 700
    print(f"  PASS: Transfer completed")

    stats = nc.get_economy_statistics()
    assert stats["total_transactions"] >= 3
    print(f"  PASS: {stats['total_transactions']} transactions recorded")

    print("  PASS: Nexus Credits operations complete\n")
    return True


async def test_persistence_roundtrip():
    """Test JSONL persistence round-trip for contract executor."""
    print("=== Test: Persistence Round-trip ===")
    reset_contract_executor()
    ex = get_contract_executor()

    c = await ex.create_contract("job_persist", "client_p", "worker_p",
                                  ContractDuration.MEDIUM,
                                  {"title": "Persist Test", "payment": 1000.0, "currency": "NPR"})
    await ex.accept_contract(c.id, "worker_p")
    await ex.start_contract(c.id, "worker_p")
    await ex.complete_contract(c.id, "worker_p")
    print(f"  Created and completed contract: {c.id}")

    # Reset and reload
    contract_id = c.id
    reset_contract_executor()
    ex2 = get_contract_executor()

    reloaded = ex2.get_contract(contract_id)
    assert reloaded is not None, f"Contract {contract_id} not found after reload"
    assert reloaded.status == "completed", f"Expected completed, got {reloaded.status}"
    print(f"  PASS: Contract reloaded with status={reloaded.status}")

    assert len(ex2.audit_trail) >= 3, f"Expected >=3 audit entries, got {len(ex2.audit_trail)}"
    print(f"  PASS: {len(ex2.audit_trail)} audit entries reloaded")

    print("  PASS: Persistence round-trip complete\n")
    return True


async def main():
    tests = [
        test_contract_executor,
        test_fsm_invalid_transition,
        test_nexus_credits,
        test_persistence_roundtrip,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
        except Exception as e:
            print(f"  FAIL: {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
