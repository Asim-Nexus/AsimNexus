"""
AsimNexus Storage — In-Memory to OLTP Migration Adapter.

Migrates critical in-memory data stores into OLTP tables, fixing the
critical audit findings where financial data (economy/nexus_credits),
blockchain state (core/blockchain/governance), and other RAM-only stores
have zero persistence.

Handles the known type bug in ``economy/nexus_credits.py`` where
``transactions`` is annotated as ``Dict`` but initialised as ``[]`` (List).
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from storage.oltp_engine import OltpEngine

logger = logging.getLogger(__name__)


# ===================================================================
# InMemoryToOltpMigrator
# ===================================================================


class InMemoryToOltpMigrator:
    """
    Migrates in-memory data stores into OLTP tables.

    Handles the critical migration of economy/credits, blockchain governance,
    and all other RAM-only data stores into the persistent OLTP layer.

    Parameters
    ----------
    oltp : OltpEngine
        An initialised OltpEngine instance to write data into.
    """

    def __init__(self, oltp: OltpEngine) -> None:
        self._oltp: OltpEngine = oltp

    # ------------------------------------------------------------------
    # Economy migration
    # ------------------------------------------------------------------

    async def migrate_economy(
        self, economy_module: Any
    ) -> Dict[str, Any]:
        """Migrate economy/credit state from in-memory to OLTP.

        Reads from ``economy_module`` (expected to be a ``NexusCredits``
        instance or compatible object) and inserts into ``credit_accounts``
        and ``credit_transactions`` tables.

        Handles the known type bug in ``nexus_credits.py`` where the
        ``transactions`` attribute is annotated as ``Dict[str, Transaction]``
        but initialised as ``[]`` (a ``List``). The migrator safely attempts
        to read this state and handles both type formats.

        Parameters
        ----------
        economy_module : Any
            A ``NexusCredits`` instance (or compatible object) with
            ``user_balances``, ``transactions``, and ``credits`` attributes.

        Returns
        -------
        Dict[str, Any]
            Report with ``accounts_migrated``, ``transactions_migrated``,
            and ``errors``.
        """
        report: Dict[str, Any] = {
            "accounts_migrated": 0,
            "transactions_migrated": 0,
            "errors": [],
        }

        try:
            # --- Migrate user balances -> credit_accounts ---
            user_balances: Dict[str, float] = getattr(
                economy_module, "user_balances", {}
            )
            if isinstance(user_balances, dict):
                for user_id, balance in user_balances.items():
                    try:
                        account_id = str(uuid.uuid4())
                        now = datetime.utcnow().isoformat()
                        await self._oltp.execute(
                            """INSERT INTO credit_accounts
                            (id, user_id, account_type, balance, currency, created_at, updated_at)
                            VALUES (?, ?, 'user', ?, 'ASIM', ?, ?)""",
                            (
                                account_id,
                                str(user_id),
                                float(balance),
                                now,
                                now,
                            ),
                        )
                        report["accounts_migrated"] += 1
                    except Exception as exc:
                        report["errors"].append(
                            f"Failed to migrate balance for user {user_id}: {exc}"
                        )
            else:
                logger.warning(
                    "user_balances is not a dict (type=%s), skipping",
                    type(user_balances).__name__,
                )

            # --- Migrate transaction history -> credit_transactions ---
            # Handle the type bug: transactions may be Dict or List
            transactions_raw = getattr(economy_module, "transactions", [])
            tx_items: List[Any] = []

            if isinstance(transactions_raw, dict):
                # If it's a dict, collect values
                tx_items = list(transactions_raw.values())
            elif isinstance(transactions_raw, (list, tuple)):
                # If it's a list (the buggy case), use as-is
                tx_items = list(transactions_raw)
            else:
                logger.warning(
                    "transactions has unexpected type %s, skipping",
                    type(transactions_raw).__name__,
                )

            for txn in tx_items:
                try:
                    # Build account_id from sender (or use a fallback)
                    sender = getattr(txn, "sender_id", None) or "unknown"
                    account_id = str(uuid.uuid4())
                    amount = float(getattr(txn, "amount", 0))
                    tx_type = self._map_transaction_type(
                        getattr(txn, "transaction_type", None)
                    )
                    status = self._map_transaction_status(
                        getattr(txn, "status", None)
                    )
                    ts = getattr(txn, "timestamp", None)
                    if hasattr(ts, "isoformat"):
                        ts = ts.isoformat()
                    elif ts is None:
                        ts = datetime.utcnow().isoformat()

                    await self._oltp.execute(
                        """INSERT INTO credit_transactions
                        (id, account_id, transaction_type, amount,
                         balance_before, balance_after, description,
                         initiated_by, status, created_at)
                        VALUES (?, ?, ?, ?, 0.0, ?, ?, ?, ?, ?)""",
                        (
                            str(uuid.uuid4()),
                            account_id,
                            tx_type,
                            amount,
                            amount,
                            f"Migrated from in-memory: {getattr(txn, 'metadata', {})}",
                            sender,
                            status,
                            ts,
                        ),
                    )
                    report["transactions_migrated"] += 1
                except Exception as exc:
                    report["errors"].append(
                        f"Failed to migrate transaction: {exc}"
                    )

            logger.info(
                "Economy migration complete: %d accounts, %d transactions",
                report["accounts_migrated"],
                report["transactions_migrated"],
            )

        except Exception as exc:
            report["errors"].append(f"Economy migration failed: {exc}")
            logger.error("Economy migration error: %s", exc)

        return report

    @staticmethod
    def _map_transaction_type(tx_type: Any) -> str:
        """Map a transaction type enum/value to a standard string."""
        if tx_type is None:
            return "transfer"
        if hasattr(tx_type, "value"):
            return str(tx_type.value)
        return str(tx_type).lower()

    @staticmethod
    def _map_transaction_status(status: Any) -> str:
        """Map a transaction status enum/value to a standard string."""
        if status is None:
            return "completed"
        if hasattr(status, "value"):
            return str(status.value)
        return str(status).lower()

    # ------------------------------------------------------------------
    # Governance migration
    # ------------------------------------------------------------------

    async def migrate_governance(
        self, governance_module: Any
    ) -> Dict[str, Any]:
        """Migrate blockchain governance state from in-memory to OLTP.

        Reads from ``governance_module`` (expected to be a
        ``BlockchainGovernance`` instance) and inserts into
        ``governance_state`` and ``governance_decisions`` tables.

        Parameters
        ----------
        governance_module : Any
            A ``BlockchainGovernance`` instance with ``chain``,
            ``smart_contracts``, ``identities``, and
            ``pending_transactions`` attributes.

        Returns
        -------
        Dict[str, Any]
            Report with ``blocks_migrated``, ``decisions_migrated``,
            ``contracts_migrated``, ``identities_migrated``, and ``errors``.
        """
        report: Dict[str, Any] = {
            "blocks_migrated": 0,
            "decisions_migrated": 0,
            "contracts_migrated": 0,
            "identities_migrated": 0,
            "errors": [],
        }

        try:
            # --- Migrate chain blocks -> governance_state ---
            chain: List[Any] = getattr(governance_module, "chain", [])
            for block in chain:
                try:
                    block_number = getattr(block, "block_number", 0)
                    prev_hash = getattr(block, "previous_hash", "")
                    block_hash = getattr(block, "hash", "")
                    transactions = getattr(block, "transactions", [])
                    ts = getattr(block, "timestamp", None)
                    if hasattr(ts, "isoformat"):
                        ts = ts.isoformat()
                    elif ts is None:
                        ts = datetime.utcnow().isoformat()

                    await self._oltp.execute(
                        """INSERT INTO governance_state
                        (id, block_number, previous_hash, hash, transactions,
                         governance_type, status, created_at, metadata)
                        VALUES (?, ?, ?, ?, ?, 'consensus', 'executed', ?, '{}')""",
                        (
                            str(uuid.uuid4()),
                            int(block_number),
                            str(prev_hash),
                            str(block_hash),
                            json.dumps(transactions, default=str),
                            ts,
                        ),
                    )
                    report["blocks_migrated"] += 1
                except Exception as exc:
                    report["errors"].append(
                        f"Failed to migrate block: {exc}"
                    )

            # --- Migrate smart contracts -> governance_decisions ---
            contracts: Dict[str, Any] = getattr(
                governance_module, "smart_contracts", {}
            )
            if isinstance(contracts, dict):
                for contract_id, contract in contracts.items():
                    try:
                        ts = getattr(contract, "timestamp", None)
                        if hasattr(ts, "isoformat"):
                            ts = ts.isoformat()
                        elif ts is None:
                            ts = datetime.utcnow().isoformat()

                        await self._oltp.execute(
                            """INSERT INTO governance_decisions
                            (id, decision_type, initiator_id, initiator_type,
                             target_sector, action, verdict, reasoning,
                             created_at)
                            VALUES (?, 'contract_deploy', ?, 'system',
                             'blockchain', 'deploy_contract', 'approved', ?, ?)""",
                            (
                                str(uuid.uuid4()),
                                contract_id,
                                json.dumps(
                                    {
                                        "code": getattr(contract, "code", ""),
                                        "state": getattr(contract, "state", {}),
                                    },
                                    default=str,
                                ),
                                ts,
                            ),
                        )
                        report["contracts_migrated"] += 1
                    except Exception as exc:
                        report["errors"].append(
                            f"Failed to migrate contract {contract_id}: {exc}"
                        )

            # --- Migrate DID identities -> did_registry ---
            identities: Dict[str, Any] = getattr(
                governance_module, "identities", {}
            )
            if isinstance(identities, dict):
                for did, identity in identities.items():
                    try:
                        public_key = getattr(identity, "public_key", "")
                        ts = getattr(identity, "timestamp", None)
                        if hasattr(ts, "isoformat"):
                            ts = ts.isoformat()
                        elif ts is None:
                            ts = datetime.utcnow().isoformat()

                        await self._oltp.execute(
                            """INSERT INTO did_registry
                            (did, public_key, controller, attributes, created_at, updated_at)
                            VALUES (?, ?, 'governance', ?, ?, ?)""",
                            (
                                str(did),
                                str(public_key),
                                json.dumps(
                                    getattr(identity, "attributes", {}),
                                    default=str,
                                ),
                                ts,
                                ts,
                            ),
                        )
                        report["identities_migrated"] += 1
                    except Exception as exc:
                        report["errors"].append(
                            f"Failed to migrate identity {did}: {exc}"
                        )

            logger.info(
                "Governance migration complete: %d blocks, %d contracts, %d identities",
                report["blocks_migrated"],
                report["contracts_migrated"],
                report["identities_migrated"],
            )

        except Exception as exc:
            report["errors"].append(f"Governance migration failed: {exc}")
            logger.error("Governance migration error: %s", exc)

        return report

    # ------------------------------------------------------------------
    # DID registry migration
    # ------------------------------------------------------------------

    async def migrate_did_registry(
        self, identity_module: Any
    ) -> Dict[str, Any]:
        """Migrate DID registry data from identity providers to OLTP.

        Parameters
        ----------
        identity_module : Any
            An identity provider instance with DID-related attributes
            (e.g. ``founder_clones``, ``identities``).

        Returns
        -------
        Dict[str, Any]
            Report with ``dids_migrated`` and ``errors``.
        """
        report: Dict[str, Any] = {
            "dids_migrated": 0,
            "errors": [],
        }

        try:
            # Try common identity provider patterns
            did_sources: List[Tuple[str, Any]] = []

            # Pattern 1: founder_clones dict
            founder_clones = getattr(identity_module, "founder_clones", {})
            if isinstance(founder_clones, dict):
                for clone_id, clone in founder_clones.items():
                    did_sources.append((str(clone_id), clone))

            # Pattern 2: identities dict (from governance)
            identities = getattr(identity_module, "identities", {})
            if isinstance(identities, dict):
                for did, identity in identities.items():
                    did_sources.append((str(did), identity))

            # Pattern 3: dids dict
            dids = getattr(identity_module, "dids", {})
            if isinstance(dids, dict):
                for did, doc in dids.items():
                    did_sources.append((str(did), doc))

            for did, source in did_sources:
                try:
                    public_key = self._extract_public_key(source)
                    now = datetime.utcnow().isoformat()

                    await self._oltp.execute(
                        """INSERT OR IGNORE INTO did_registry
                        (did, public_key, controller, created_at, updated_at)
                        VALUES (?, ?, 'migrated', ?, ?)""",
                        (did, public_key, now, now),
                    )
                    report["dids_migrated"] += 1
                except Exception as exc:
                    report["errors"].append(
                        f"Failed to migrate DID {did}: {exc}"
                    )

            logger.info(
                "DID registry migration complete: %d DIDs",
                report["dids_migrated"],
            )

        except Exception as exc:
            report["errors"].append(f"DID registry migration failed: {exc}")
            logger.error("DID registry migration error: %s", exc)

        return report

    @staticmethod
    def _extract_public_key(source: Any) -> str:
        """Extract a public key string from various identity formats."""
        if isinstance(source, dict):
            return str(source.get("public_key", source.get("pubkey", "")))
        return str(getattr(source, "public_key", getattr(source, "pubkey", "")))

    # ------------------------------------------------------------------
    # Node registry migration
    # ------------------------------------------------------------------

    async def migrate_node_registry(
        self, registry_module: Any
    ) -> Dict[str, Any]:
        """Migrate mesh node registry data to OLTP.

        Parameters
        ----------
        registry_module : Any
            A mesh node registry instance with node data
            (e.g. ``nodes`` dict, ``all_nodes()`` method).

        Returns
        -------
        Dict[str, Any]
            Report with ``nodes_migrated`` and ``errors``.
        """
        report: Dict[str, Any] = {
            "nodes_migrated": 0,
            "errors": [],
        }

        try:
            nodes: Dict[str, Any] = {}

            # Try multiple patterns for node data access
            nodes_attr = getattr(registry_module, "nodes", None)
            if isinstance(nodes_attr, dict):
                nodes = nodes_attr
            else:
                # Try all_nodes() method
                all_nodes_method = getattr(
                    registry_module, "all_nodes", None
                )
                if callable(all_nodes_method):
                    result = all_nodes_method()
                    if isinstance(result, dict):
                        nodes = result
                    elif isinstance(result, list):
                        for node in result:
                            nid = self._extract_node_id(node)
                            if nid:
                                nodes[nid] = node

            for node_id, node_data in nodes.items():
                try:
                    now = datetime.utcnow().isoformat()
                    node_type = self._extract_attr(node_data, "node_type", "peer")
                    host = self._extract_attr(node_data, "host", "")
                    public_key = self._extract_attr(
                        node_data, "public_key", ""
                    )
                    region = self._extract_attr(node_data, "region", "")
                    trust_score = float(
                        self._extract_attr(node_data, "trust_score", 0.5)
                    )
                    is_active = bool(
                        self._extract_attr(node_data, "is_active", True)
                    )
                    capabilities = self._extract_attr(
                        node_data, "capabilities", []
                    )
                    metadata = self._extract_attr(
                        node_data, "metadata", {}
                    )

                    await self._oltp.execute(
                        """INSERT OR IGNORE INTO node_registry
                        (node_id, node_type, host, public_key, region,
                         trust_score, is_active, capabilities, metadata,
                         registered_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            str(node_id),
                            node_type,
                            host,
                            public_key,
                            region,
                            trust_score,
                            1 if is_active else 0,
                            json.dumps(capabilities, default=str),
                            json.dumps(metadata, default=str),
                            now,
                        ),
                    )
                    report["nodes_migrated"] += 1
                except Exception as exc:
                    report["errors"].append(
                        f"Failed to migrate node {node_id}: {exc}"
                    )

            logger.info(
                "Node registry migration complete: %d nodes",
                report["nodes_migrated"],
            )

        except Exception as exc:
            report["errors"].append(
                f"Node registry migration failed: {exc}"
            )
            logger.error("Node registry migration error: %s", exc)

        return report

    # ------------------------------------------------------------------
    # Federation migration
    # ------------------------------------------------------------------

    async def migrate_federation(
        self, federation_module: Any
    ) -> Dict[str, Any]:
        """Migrate federation peer state to OLTP.

        Parameters
        ----------
        federation_module : Any
            A federation manager instance with peer data
            (e.g. ``peers`` dict, ``get_peers()`` method).

        Returns
        -------
        Dict[str, Any]
            Report with ``peers_migrated`` and ``errors``.
        """
        report: Dict[str, Any] = {
            "peers_migrated": 0,
            "errors": [],
        }

        try:
            peers: Dict[str, Any] = {}

            # Try multiple patterns
            peers_attr = getattr(federation_module, "peers", None)
            if isinstance(peers_attr, dict):
                peers = peers_attr
            else:
                # Try get_peers() method
                get_peers_method = getattr(
                    federation_module, "get_peers", None
                )
                if callable(get_peers_method):
                    result = get_peers_method()
                    if isinstance(result, dict):
                        peers = result
                    elif isinstance(result, list):
                        for peer in result:
                            pid = self._extract_attr(
                                peer, "peer_id", self._extract_attr(peer, "id", None)
                            )
                            if pid:
                                peers[str(pid)] = peer

            for peer_id, peer_data in peers.items():
                try:
                    now = datetime.utcnow().isoformat()
                    peer_did = self._extract_attr(
                        peer_data, "peer_did",
                        self._extract_attr(peer_data, "did", str(peer_id)),
                    )
                    peer_url = self._extract_attr(peer_data, "peer_url", "")
                    peer_name = self._extract_attr(
                        peer_data, "peer_name",
                        self._extract_attr(peer_data, "name", ""),
                    )
                    status = self._extract_attr(
                        peer_data, "status", "active"
                    )
                    trust_level = float(
                        self._extract_attr(peer_data, "trust_level", 0.3)
                    )
                    capabilities = self._extract_attr(
                        peer_data, "capabilities", []
                    )
                    metadata = self._extract_attr(
                        peer_data, "metadata", {}
                    )

                    await self._oltp.execute(
                        """INSERT OR IGNORE INTO federation_state
                        (federation_id, peer_did, peer_url, peer_name,
                         status, trust_level, capabilities, metadata,
                         joined_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            str(uuid.uuid4()),
                            peer_did,
                            peer_url,
                            peer_name,
                            status,
                            trust_level,
                            json.dumps(capabilities, default=str),
                            json.dumps(metadata, default=str),
                            now,
                        ),
                    )
                    report["peers_migrated"] += 1
                except Exception as exc:
                    report["errors"].append(
                        f"Failed to migrate peer {peer_id}: {exc}"
                    )

            logger.info(
                "Federation migration complete: %d peers",
                report["peers_migrated"],
            )

        except Exception as exc:
            report["errors"].append(
                f"Federation migration failed: {exc}"
            )
            logger.error("Federation migration error: %s", exc)

        return report

    # ------------------------------------------------------------------
    # All-in-one migration
    # ------------------------------------------------------------------

    async def migrate_all(
        self, modules: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """Run all migrations across the provided modules.

        Parameters
        ----------
        modules : Dict[str, Any]
            Mapping of module names to module instances. Expected keys:
            - ``economy``: A ``NexusCredits`` instance
            - ``governance``: A ``BlockchainGovernance`` instance
            - ``identity``: An identity provider instance
            - ``node_registry``: A mesh node registry instance
            - ``federation``: A federation manager instance

        Returns
        -------
        Dict[str, Dict[str, Any]]
            Mapping of module name to its migration report.
        """
        results: Dict[str, Dict[str, Any]] = {}

        # Economy migration
        if "economy" in modules:
            logger.info("Starting economy migration...")
            results["economy"] = await self.migrate_economy(
                modules["economy"]
            )

        # Governance migration
        if "governance" in modules:
            logger.info("Starting governance migration...")
            results["governance"] = await self.migrate_governance(
                modules["governance"]
            )

        # DID registry migration
        if "identity" in modules:
            logger.info("Starting DID registry migration...")
            results["identity"] = await self.migrate_did_registry(
                modules["identity"]
            )

        # Node registry migration
        if "node_registry" in modules:
            logger.info("Starting node registry migration...")
            results["node_registry"] = await self.migrate_node_registry(
                modules["node_registry"]
            )

        # Federation migration
        if "federation" in modules:
            logger.info("Starting federation migration...")
            results["federation"] = await self.migrate_federation(
                modules["federation"]
            )

        # Log summary
        total_migrated = sum(
            r.get("accounts_migrated", 0)
            + r.get("transactions_migrated", 0)
            + r.get("blocks_migrated", 0)
            + r.get("dids_migrated", 0)
            + r.get("nodes_migrated", 0)
            + r.get("peers_migrated", 0)
            for r in results.values()
        )
        total_errors = sum(len(r.get("errors", [])) for r in results.values())
        logger.info(
            "All migrations complete: %d items migrated, %d errors",
            total_migrated,
            total_errors,
        )

        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_attr(
        obj: Any, attr: str, default: Any = None
    ) -> Any:
        """Extract an attribute from a dict or object."""
        if isinstance(obj, dict):
            return obj.get(attr, default)
        return getattr(obj, attr, default)

    @staticmethod
    def _extract_node_id(node: Any) -> Optional[str]:
        """Extract a node identifier from various node formats."""
        if isinstance(node, dict):
            return str(
                node.get(
                    "node_id",
                    node.get("id", node.get("nodeId", "")),
                )
            )
        node_id = getattr(
            node, "node_id", getattr(node, "id", getattr(node, "nodeId", None))
        )
        return str(node_id) if node_id else None
