#!/usr/bin/env python3
"""
Federation CLI — AsimNexus Federation Management Command-Line Interface.

Provides commands to manage federation peers, proposals, state sync,
governance audit, cross-border compliance, and heartbeat health.

Usage:
    python scripts/manage_federation.py --help
    python scripts/manage_federation.py status
    python scripts/manage_federation.py peers list
    python scripts/manage_federation.py propose join --did did:asim:peer1 --endpoint https://peer1.example
    python scripts/manage_federation.py approve <proposal_id>
    python scripts/manage_federation.py sync --peer <peer_did>
    python scripts/manage_federation.py audit query --action peer_join_approved
    python scripts/manage_federation.py compliance check \
        --classification CONFIDENTIAL --from NP --to EU
    python scripts/manage_federation.py health
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

# Ensure the parent directory is on the path so we can import core.*
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s | %(message)s",
)


# ---------------------------------------------------------------------------
# Async command dispatcher
# ---------------------------------------------------------------------------

async def async_main(args: argparse.Namespace) -> None:
    """Dispatch to the appropriate async command handler."""
    command = args.command

    if command == "status":
        await cmd_status(args)
    elif command == "peers":
        if args.peer_action == "list":
            await cmd_peer_list(args)
        elif args.peer_action == "add":
            await cmd_peer_add(args)
        elif args.peer_action == "remove":
            await cmd_peer_remove(args)
        else:
            print(f"Unknown peer action: {args.peer_action}")
    elif command == "propose":
        if args.propose_action == "join":
            await cmd_propose_join(args)
        else:
            print(f"Unknown propose action: {args.propose_action}")
    elif command == "approve":
        await cmd_approve(args)
    elif command == "reject":
        await cmd_reject(args)
    elif command == "sync":
        await cmd_sync(args)
    elif command == "audit":
        if args.audit_action == "query":
            await cmd_audit_query(args)
        elif args.audit_action == "verify":
            await cmd_audit_verify(args)
        elif args.audit_action == "stats":
            await cmd_audit_stats(args)
        else:
            print(f"Unknown audit action: {args.audit_action}")
    elif command == "compliance":
        if args.compliance_action == "check":
            await cmd_compliance_check(args)
        elif args.compliance_action == "report":
            await cmd_compliance_report(args)
        elif args.compliance_action == "rules":
            await cmd_compliance_rules(args)
        else:
            print(f"Unknown compliance action: {args.compliance_action}")
    elif command == "health":
        await cmd_health(args)
    elif command == "consensus":
        if args.consensus_action == "propose":
            await cmd_consensus_propose(args)
        else:
            print(f"Unknown consensus action: {args.consensus_action}")
    else:
        print(f"Unknown command: {command}")


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

async def cmd_status(args: argparse.Namespace) -> None:
    """Show federation status."""
    from core.federation.global_federation_governor import (
        get_global_federation_governor,
    )

    governor = await get_global_federation_governor()
    status = governor.get_federation_status()
    _print_json(status)


async def cmd_peer_list(args: argparse.Namespace) -> None:
    """List federation peers."""
    from core.federation.global_federation_governor import (
        get_global_federation_governor,
    )

    governor = await get_global_federation_governor()
    peers = governor.peer_list()
    if not peers:
        print("No peers in federation.")
        return
    print(f"Total peers: {len(peers)}")
    for p in peers:
        print(f"  {p.get('peer_id', '?'):16s}  {p.get('did', ''):30s}  "
              f"trusted={p.get('trusted', False)}")


async def cmd_peer_add(args: argparse.Namespace) -> None:
    """Add a peer to the federation."""
    from core.federation.global_federation import get_federation

    mgr = get_federation()
    mgr.add_peer(did=args.did, endpoint=args.endpoint, trusted=args.trusted)
    print(f"Peer {args.did} added (trusted={args.trusted})")


async def cmd_peer_remove(args: argparse.Namespace) -> None:
    """Remove a peer from the federation."""
    from core.federation.global_federation_governor import (
        get_global_federation_governor,
    )

    governor = await get_global_federation_governor()
    result = await governor.leave_federation(args.did)
    if result:
        print(f"Peer {args.did} removed.")
    else:
        print(f"Peer {args.did} not found.")


async def cmd_propose_join(args: argparse.Namespace) -> None:
    """Propose a new peer to join the federation."""
    from core.federation.global_federation_governor import (
        get_global_federation_governor,
    )

    governor = await get_global_federation_governor()
    proposal = await governor.propose_join(
        did=args.did,
        endpoint=args.endpoint,
        peer_name=args.name or args.did,
        trust_level=args.trust_level.upper(),
    )
    print(f"Proposal created: {proposal.proposal_id}")
    print(f"  Peer DID:  {proposal.peer_did}")
    print(f"  Peer URL:  {proposal.peer_url}")
    print(f"  Status:    {proposal.status.value}")
    if proposal.consensus_round_id:
        print(f"  Consensus: {proposal.consensus_round_id}")


async def cmd_approve(args: argparse.Namespace) -> None:
    """Approve a pending join proposal."""
    from core.federation.global_federation_governor import (
        get_global_federation_governor,
    )

    governor = await get_global_federation_governor()
    result = await governor.approve_join(args.proposal_id, approved_by=args.approved_by or "cli")
    if result:
        print(f"Proposal {args.proposal_id} approved.")
        _print_json(result)
    else:
        print(f"Proposal {args.proposal_id} not found or not pending.")


async def cmd_reject(args: argparse.Namespace) -> None:
    """Reject a pending join proposal."""
    from core.federation.global_federation_governor import (
        get_global_federation_governor,
    )

    governor = await get_global_federation_governor()
    result = await governor.reject_join(args.proposal_id, reason=args.reason or "Rejected via CLI")
    if result:
        print(f"Proposal {args.proposal_id} rejected.")
    else:
        print(f"Proposal {args.proposal_id} not found or not pending.")


async def cmd_sync(args: argparse.Namespace) -> None:
    """Trigger a state sync with a peer."""
    from core.federation.global_federation_governor import (
        get_global_federation_governor,
    )
    from core.federation.federation_protocol_enhanced import SyncScope

    governor = await get_global_federation_governor()
    scope = SyncScope(args.scope) if args.scope else SyncScope.DELTA_ONLY
    message = await governor.sync_state(
        peer_did=args.peer,
        scope=scope,
    )
    if message:
        print(f"Sync message created for peer {args.peer}")
        print(f"  Message ID: {message.message_id}")
        print(f"  Scope:      {message.scope.value}")
        print(f"  Packet keys: {list(message.state_packet.keys()) if message.state_packet else 'empty'}")
    else:
        print(f"Failed to create sync message for peer {args.peer}")


async def cmd_audit_query(args: argparse.Namespace) -> None:
    """Query the governance audit trail."""
    from governance.governance_audit import get_governance_audit

    audit = await get_governance_audit()
    entries = await audit.query(
        action=args.action,
        actor=args.actor,
        resource=args.resource,
        severity=args.severity,
        limit=args.limit,
    )
    if not entries:
        print("No matching audit entries.")
        return
    print(f"Found {len(entries)} audit entries:")
    for e in entries:
        ts = e.get("timestamp", 0)
        print(f"  [{e.get('entry_id', '?'):20s}] {e.get('action', '?'):30s}  "
              f"actor={e.get('actor', ''):20s}  "
              f"hash={e.get('entry_hash', '')[:12]}...")


async def cmd_audit_verify(args: argparse.Namespace) -> None:
    """Verify the integrity of the audit chain."""
    from governance.governance_audit import get_governance_audit

    audit = await get_governance_audit()
    report = await audit.verify_chain()
    if report["status"] == "intact":
        print(f"✓ Audit chain INTACT ({report['total_entries']} entries)")
    elif report["status"] == "empty":
        print("Audit chain is empty.")
    else:
        print(f"✗ Audit chain BROKEN ({len(report['broken_links'])} broken links)")
        for link in report["broken_links"]:
            print(f"  - Entry {link['entry_id']}: {link['reason']}")


async def cmd_audit_stats(args: argparse.Namespace) -> None:
    """Show audit trail statistics."""
    from governance.governance_audit import get_governance_audit

    audit = await get_governance_audit()
    stats = await audit.get_stats()
    _print_json(stats)


async def cmd_compliance_check(args: argparse.Namespace) -> None:
    """Check a cross-border data flow."""
    from governance.cross_border_compliance import get_cross_border_compliance

    cbc = await get_cross_border_compliance()
    await cbc.start()

    result = await cbc.check_cross_border_data_flow(
        data_classification=args.classification,
        origin_jurisdiction=args.origin,
        destination_jurisdiction=args.destination,
        purpose=args.purpose or "",
        actor_did=args.actor or "",
    )
    _print_json(result)


async def cmd_compliance_report(args: argparse.Namespace) -> None:
    """Show cross-border compliance report."""
    from governance.cross_border_compliance import get_cross_border_compliance

    cbc = await get_cross_border_compliance()
    report = await cbc.get_compliance_report()
    _print_json(report)


async def cmd_compliance_rules(args: argparse.Namespace) -> None:
    """List regional compliance rules."""
    from governance.cross_border_compliance import get_cross_border_compliance

    cbc = await get_cross_border_compliance()
    rules = cbc.get_regional_rules()
    if not rules:
        print("No regional rules registered.")
        return
    print(f"Total regional rules: {len(rules)}")
    for r in rules:
        print(f"  [{r.get('jurisdiction', '?'):4s}] {r.get('framework', '?'):20s}  "
              f"class={r.get('data_classification', ''):12s}  "
              f"sovereignty={r.get('sovereignty_policy', '')}")


async def cmd_health(args: argparse.Namespace) -> None:
    """Show heartbeat health for all peers."""
    from core.federation.global_federation_governor import (
        get_global_federation_governor,
    )

    governor = await get_global_federation_governor()
    health = governor._heartbeat.get_all_health()
    if not health:
        print("No peers registered for health monitoring.")
        return
    print(f"Monitored peers: {len(health)}")
    for pid, h in health.items():
        print(f"  {pid:20s}  status={h['status']:12s}  "
              f"missed={h['missed_beats']}  "
              f"latency={h['latency_ms']:.1f}ms")


async def cmd_consensus_propose(args: argparse.Namespace) -> None:
    """Propose a federation decision via consensus."""
    from core.federation.global_federation_governor import (
        get_global_federation_governor,
    )

    governor = await get_global_federation_governor()
    result = await governor.propose_federation_decision(
        topic=args.topic,
        description=args.description,
        decision_level=args.level.upper(),
    )
    if result:
        print(f"Consensus proposal created:")
        _print_json(result)
    else:
        print("Failed to create consensus proposal (no consensus engine available).")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _print_json(data: Any) -> None:
    """Pretty-print a dict as JSON."""
    print(json.dumps(data, indent=2, default=str, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="manage_federation",
        description="AsimNexus Federation Management CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- status ---
    p_status = sub.add_parser("status", help="Show federation status")

    # --- peers ---
    p_peers = sub.add_parser("peers", help="Manage federation peers")
    p_peers_sub = p_peers.add_subparsers(dest="peer_action", required=True)

    p_peers_list = p_peers_sub.add_parser("list", help="List all peers")
    p_peers_add = p_peers_sub.add_parser("add", help="Add a peer directly")
    p_peers_add.add_argument("--did", required=True, help="Peer DID")
    p_peers_add.add_argument("--endpoint", required=True, help="Peer endpoint URL")
    p_peers_add.add_argument("--trusted", action="store_true", default=False, help="Mark as trusted")
    p_peers_remove = p_peers_sub.add_parser("remove", help="Remove a peer")
    p_peers_remove.add_argument("did", help="Peer DID to remove")

    # --- propose ---
    p_propose = sub.add_parser("propose", help="Create proposals")
    p_propose_sub = p_propose.add_subparsers(dest="propose_action", required=True)

    p_join = p_propose_sub.add_parser("join", help="Propose a peer to join")
    p_join.add_argument("--did", required=True, help="Peer DID")
    p_join.add_argument("--endpoint", required=True, help="Peer endpoint URL")
    p_join.add_argument("--name", default="", help="Peer display name")
    p_join.add_argument("--trust-level", default="VERIFIED",
                        choices=["UNTRUSTED", "BASIC", "VERIFIED", "TRUSTED", "CO_SIGNATURE"],
                        help="Trust level for the new peer")

    # --- approve / reject ---
    p_approve = sub.add_parser("approve", help="Approve a join proposal")
    p_approve.add_argument("proposal_id", help="Proposal ID to approve")
    p_approve.add_argument("--approved-by", default="", help="Approver identifier")

    p_reject = sub.add_parser("reject", help="Reject a join proposal")
    p_reject.add_argument("proposal_id", help="Proposal ID to reject")
    p_reject.add_argument("--reason", default="Rejected via CLI", help="Rejection reason")

    # --- sync ---
    p_sync = sub.add_parser("sync", help="Trigger state sync with a peer")
    p_sync.add_argument("--peer", required=True, help="Peer DID to sync with")
    p_sync.add_argument("--scope", default="delta_only",
                        choices=["delta_only", "full_state", "consensus_only", "governance_only"],
                        help="Sync scope")

    # --- audit ---
    p_audit = sub.add_parser("audit", help="Governance audit trail")
    p_audit_sub = p_audit.add_subparsers(dest="audit_action", required=True)

    p_audit_query = p_audit_sub.add_parser("query", help="Query audit entries")
    p_audit_query.add_argument("--action", default="", help="Filter by action")
    p_audit_query.add_argument("--actor", default="", help="Filter by actor")
    p_audit_query.add_argument("--resource", default="", help="Filter by resource")
    p_audit_query.add_argument("--severity", default="", help="Filter by severity")
    p_audit_query.add_argument("--limit", type=int, default=20, help="Max results")

    p_audit_verify = p_audit_sub.add_parser("verify", help="Verify audit chain integrity")
    p_audit_stats = p_audit_sub.add_parser("stats", help="Audit trail statistics")

    # --- compliance ---
    p_compliance = sub.add_parser("compliance", help="Cross-border compliance")
    p_compliance_sub = p_compliance.add_subparsers(dest="compliance_action", required=True)

    p_comp_check = p_compliance_sub.add_parser("check", help="Check cross-border data flow")
    p_comp_check.add_argument("--classification", required=True,
                              choices=["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED", "SECRET"],
                              help="Data classification")
    p_comp_check.add_argument("--from", dest="origin", required=True, help="Origin jurisdiction (e.g. NP)")
    p_comp_check.add_argument("--to", dest="destination", required=True, help="Destination jurisdiction")
    p_comp_check.add_argument("--purpose", default="", help="Purpose of data flow")
    p_comp_check.add_argument("--actor", default="", help="Acting entity DID")

    p_comp_report = p_compliance_sub.add_parser("report", help="Compliance report")
    p_comp_rules = p_compliance_sub.add_parser("rules", help="List regional compliance rules")

    # --- health ---
    p_health = sub.add_parser("health", help="Show heartbeat health")

    # --- consensus ---
    p_consensus = sub.add_parser("consensus", help="Federation consensus")
    p_consensus_sub = p_consensus.add_subparsers(dest="consensus_action", required=True)

    p_cons_propose = p_consensus_sub.add_parser("propose", help="Propose federation decision")
    p_cons_propose.add_argument("--topic", required=True, help="Decision topic")
    p_cons_propose.add_argument("--description", required=True, help="Decision description")
    p_cons_propose.add_argument("--level", default="HIGH",
                                choices=["LOW", "HIGH", "CRITICAL", "SOVEREIGNTY"],
                                help="Decision level")

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()
    try:
        asyncio.run(async_main(args))
    except KeyboardInterrupt:
        print("\nInterrupted.")
        sys.exit(1)
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
