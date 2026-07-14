#!/usr/bin/env python3
"""
Digital Twin Marketplace — Agent Mode: Give Work & Do Work
===========================================================

Implements the "हरेक मानिसको आफ्नो Digital Twin/Clone" vision where:
  - Every person's Digital Twin/Clone can work for others
  - Work types: coding, video, music, design, and any digital service
  - 5/15/30 day contracts with 3-confirmation
  - Agent Mode (Public/Private): Clone works autonomously with human oversight
  - Escrow system: Secure payment holding until work completion
  - Reputation system: Trust-based marketplace with staking

Key Concepts:
  - Agent Listing: A user publishes their Digital Twin's capabilities as a service
  - Agent Contract: Time-bound authority for the Twin to perform work (5/15/30 days)
  - 3-Confirmation: Level-1 (PIN), Level-2 (OTP/MFA), Level-3 (HSM + Biometric)
  - Escrow: Payment held in escrow until work is verified complete
  - Reputation Staking: Agents stake reputation to signal quality
  - Mode Integration: Works across Citizen, Company, and Hybrid modes

Integrates with:
  - core/agent_contract.py — 5/15/30 day agent contracts
  - core/nexus_connector.py — Mode routing and cross-consent
  - core/identity/enhanced_federated_identity.py — Multi-mode Digital Twins
  - core/security/level3_confirmation.py — 3-layer human verification
  - core/mirror/mirror_module.py — Digital Twin consciousness
  - core/economy/escrow.py — Secure payment holding
"""

import os
import time
import json
import uuid
import hashlib
import logging
import threading
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta

logger = logging.getLogger("AsimNexus.Marketplace.DigitalTwin")

# ─── Environment Configuration ────────────────────────────────────────────────
_DTM_DB_PATH = os.getenv(
    "ASIM_DTM_DB_PATH",
    "data/digital_twin_marketplace.jsonl",
)
os.makedirs(os.path.dirname(_DTM_DB_PATH) if os.path.dirname(_DTM_DB_PATH) else ".", exist_ok=True)

# ─── Enums ────────────────────────────────────────────────────────────────────

class AgentListingStatus(str, Enum):
    """Status of an agent listing in the marketplace."""
    DRAFT = "draft"               # Being created, not yet published
    ACTIVE = "active"             # Available for hire
    ENGAGED = "engaged"           # Currently working on a contract
    PAUSED = "paused"             # Temporarily unavailable
    ARCHIVED = "archived"         # No longer available

class WorkCategory(str, Enum):
    """Categories of work a Digital Twin can perform."""
    CODING = "coding"             # Software development
    VIDEO = "video"               # Video production/editing
    MUSIC = "music"               # Music composition/production
    DESIGN = "design"             # Graphic design, UI/UX
    WRITING = "writing"           # Content writing, translation
    ANALYSIS = "analysis"         # Data analysis, research
    EDUCATION = "education"       # Teaching, tutoring
    CONSULTING = "consulting"     # Business/technical consulting
    ADMIN = "admin"               # Administrative tasks
    CUSTOM = "custom"             # Custom/other services

class AgentMode(str, Enum):
    """How the Digital Twin operates when working."""
    PUBLIC = "public"             # Twin works autonomously, visible to all
    PRIVATE = "private"           # Twin works with human oversight, limited visibility
    HYBRID = "hybrid"             # Twin works autonomously but human can intervene

class ContractTier(str, Enum):
    """Duration tiers for agent contracts in the marketplace."""
    TRIAL = "trial"               # 5 days — limited scope, high oversight
    STANDARD = "standard"         # 15 days — standard scope
    EXTENDED = "extended"         # 30 days — full scope, periodic audit

class EscrowStatus(str, Enum):
    """Status of an escrow payment."""
    PENDING = "pending"           # Funds deposited, work in progress
    RELEASED = "released"         # Funds released to agent
    REFUNDED = "refunded"         # Funds refunded to client
    DISPUTED = "disputed"         # Under dispute resolution
    PARTIAL = "partial"           # Partial release, partial refund

class ConfirmationLevel(str, Enum):
    """3-Confirmation levels for marketplace actions."""
    LEVEL_1 = "level_1"           # PIN confirmation
    LEVEL_2 = "level_2"           # OTP/MFA confirmation
    LEVEL_3 = "level_3"           # HSM + Biometric confirmation

# ─── Data Classes ─────────────────────────────────────────────────────────────

@dataclass
class AgentListing:
    """A Digital Twin's service listing in the marketplace."""
    listing_id: str
    user_id: str                    # Owner of the Digital Twin
    twin_id: str                    # The Digital Twin offering services
    mode: str                       # Citizen/Company/Hybrid mode
    title: str                      # Service title
    description: str                # Service description
    category: WorkCategory          # Type of work
    agent_mode: AgentMode           # Public/Private/Hybrid
    skills: List[str]               # Skills/tags
    portfolio: List[str]            # Portfolio links/refs
    price_min: float                # Minimum price
    price_max: float                # Maximum price
    currency: str = "NPR"           # Currency (NPR default for Nepal)
    status: AgentListingStatus = AgentListingStatus.DRAFT
    rating: float = 0.0             # Average rating
    total_contracts: int = 0        # Completed contracts count
    reputation_stake: float = 0.0   # Amount of reputation staked
    created_at: float = 0.0
    updated_at: float = 0.0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "listing_id": self.listing_id,
            "user_id": self.user_id,
            "twin_id": self.twin_id,
            "mode": self.mode,
            "title": self.title,
            "description": self.description,
            "category": self.category.value if isinstance(self.category, WorkCategory) else self.category,
            "agent_mode": self.agent_mode.value if isinstance(self.agent_mode, AgentMode) else self.agent_mode,
            "skills": self.skills,
            "portfolio": self.portfolio,
            "price_min": self.price_min,
            "price_max": self.price_max,
            "currency": self.currency,
            "status": self.status.value if isinstance(self.status, AgentListingStatus) else self.status,
            "rating": self.rating,
            "total_contracts": self.total_contracts,
            "reputation_stake": self.reputation_stake,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentListing":
        """Create from dictionary, handling enum fields."""
        if "category" in data and isinstance(data["category"], str):
            try:
                data["category"] = WorkCategory(data["category"])
            except ValueError:
                data["category"] = WorkCategory.CUSTOM
        if "agent_mode" in data and isinstance(data["agent_mode"], str):
            try:
                data["agent_mode"] = AgentMode(data["agent_mode"])
            except ValueError:
                data["agent_mode"] = AgentMode.PRIVATE
        if "status" in data and isinstance(data["status"], str):
            try:
                data["status"] = AgentListingStatus(data["status"])
            except ValueError:
                data["status"] = AgentListingStatus.DRAFT
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class MarketplaceContract:
    """A work contract between a Client and an Agent (Digital Twin)."""
    contract_id: str
    listing_id: str                 # The listing this contract is for
    client_id: str                  # Person hiring (user_id)
    agent_id: str                   # Digital Twin owner (user_id)
    twin_id: str                    # The Digital Twin doing the work
    title: str                      # Contract title
    description: str                # Scope of work
    tier: ContractTier              # TRIAL/STANDARD/EXTENDED
    price: float                    # Agreed price
    currency: str = "NPR"
    escrow_id: str = ""             # Escrow transaction ID
    status: str = "proposed"        # proposed → confirmed → active → completed/cancelled
    confirmation_level: ConfirmationLevel = ConfirmationLevel.LEVEL_1
    confirmation_data: Dict[str, Any] = field(default_factory=dict)
    milestones: List[Dict[str, Any]] = field(default_factory=list)
    deliverables: List[str] = field(default_factory=list)
    client_rating: float = 0.0      # Rating given by client
    agent_rating: float = 0.0       # Rating given by agent
    dispute_reason: str = ""
    created_at: float = 0.0
    updated_at: float = 0.0
    completed_at: float = 0.0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()
        if not self.updated_at:
            self.updated_at = self.created_at

    @property
    def duration_days(self) -> int:
        """Get the duration in days based on tier."""
        return {"trial": 5, "standard": 15, "extended": 30}.get(self.tier.value if isinstance(self.tier, ContractTier) else self.tier, 5)

    @property
    def expires_at(self) -> float:
        """Get the expiry timestamp."""
        return self.created_at + (self.duration_days * 86400)

    def is_expired(self) -> bool:
        """Check if the contract has expired."""
        return time.time() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "listing_id": self.listing_id,
            "client_id": self.client_id,
            "agent_id": self.agent_id,
            "twin_id": self.twin_id,
            "title": self.title,
            "description": self.description,
            "tier": self.tier.value if isinstance(self.tier, ContractTier) else self.tier,
            "price": self.price,
            "currency": self.currency,
            "escrow_id": self.escrow_id,
            "status": self.status,
            "confirmation_level": self.confirmation_level.value if isinstance(self.confirmation_level, ConfirmationLevel) else self.confirmation_level,
            "confirmation_data": self.confirmation_data,
            "milestones": self.milestones,
            "deliverables": self.deliverables,
            "client_rating": self.client_rating,
            "agent_rating": self.agent_rating,
            "dispute_reason": self.dispute_reason,
            "duration_days": self.duration_days,
            "expires_at": self.expires_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MarketplaceContract":
        """Create from dictionary, handling enum fields."""
        if "tier" in data and isinstance(data["tier"], str):
            try:
                data["tier"] = ContractTier(data["tier"])
            except ValueError:
                data["tier"] = ContractTier.TRIAL
        if "confirmation_level" in data and isinstance(data["confirmation_level"], str):
            try:
                data["confirmation_level"] = ConfirmationLevel(data["confirmation_level"])
            except ValueError:
                data["confirmation_level"] = ConfirmationLevel.LEVEL_1
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class EscrowTransaction:
    """Secure payment holding for marketplace contracts."""
    escrow_id: str
    contract_id: str
    client_id: str
    agent_id: str
    amount: float
    currency: str = "NPR"
    status: EscrowStatus = EscrowStatus.PENDING
    deposit_tx: str = ""            # Deposit transaction reference
    release_tx: str = ""            # Release transaction reference
    dispute_id: str = ""            # Dispute reference if disputed
    created_at: float = 0.0
    updated_at: float = 0.0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "escrow_id": self.escrow_id,
            "contract_id": self.contract_id,
            "client_id": self.client_id,
            "agent_id": self.agent_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status.value if isinstance(self.status, EscrowStatus) else self.status,
            "deposit_tx": self.deposit_tx,
            "release_tx": self.release_tx,
            "dispute_id": self.dispute_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "EscrowTransaction":
        if "status" in data and isinstance(data["status"], str):
            try:
                data["status"] = EscrowStatus(data["status"])
            except ValueError:
                data["status"] = EscrowStatus.PENDING
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ─── Digital Twin Marketplace ─────────────────────────────────────────────────

class DigitalTwinMarketplace:
    """
    The marketplace where Digital Twins offer services and humans hire them.

    Implements the full "Give Work & Do Work" lifecycle:
      1. Agent creates a listing (publishes their Twin's capabilities)
      2. Client discovers and hires the agent
      3. Contract is created with 3-confirmation
      4. Escrow holds payment
      5. Agent's Twin performs the work (Agent Mode)
      6. Milestones are delivered and verified
      7. Escrow is released upon completion
      8. Ratings are exchanged
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._listings: Dict[str, AgentListing] = {}       # listing_id → AgentListing
        self._contracts: Dict[str, MarketplaceContract] = {}  # contract_id → MarketplaceContract
        self._escrows: Dict[str, EscrowTransaction] = {}     # escrow_id → EscrowTransaction
        self._user_listings: Dict[str, Set[str]] = {}        # user_id → {listing_ids}
        self._user_contracts: Dict[str, Set[str]] = {}       # user_id → {contract_ids}
        self._category_index: Dict[str, Set[str]] = {}       # category → {listing_ids}
        self._load_from_db()

    # ─── Listing Management ─────────────────────────────────────────────────

    def create_listing(
        self,
        user_id: str,
        twin_id: str,
        mode: str,
        title: str,
        description: str,
        category: WorkCategory,
        agent_mode: AgentMode = AgentMode.PRIVATE,
        skills: Optional[List[str]] = None,
        portfolio: Optional[List[str]] = None,
        price_min: float = 0.0,
        price_max: float = 0.0,
        currency: str = "NPR",
    ) -> AgentListing:
        """Create a new Digital Twin service listing."""
        listing = AgentListing(
            listing_id=f"dtm_{uuid.uuid4().hex[:16]}",
            user_id=user_id,
            twin_id=twin_id,
            mode=mode,
            title=title,
            description=description,
            category=category,
            agent_mode=agent_mode,
            skills=skills or [],
            portfolio=portfolio or [],
            price_min=price_min,
            price_max=price_max,
            currency=currency,
            status=AgentListingStatus.DRAFT,
        )
        with self._lock:
            self._listings[listing.listing_id] = listing
            self._user_listings.setdefault(user_id, set()).add(listing.listing_id)
            cat_key = category.value if isinstance(category, WorkCategory) else category
            self._category_index.setdefault(cat_key, set()).add(listing.listing_id)
            self._persist_listing(listing)
        logger.info(f"Listing created: {listing.listing_id} by {user_id}")
        return listing

    def publish_listing(self, listing_id: str, user_id: str) -> bool:
        """Publish a listing (DRAFT → ACTIVE)."""
        with self._lock:
            listing = self._listings.get(listing_id)
            if not listing or listing.user_id != user_id:
                return False
            if listing.status != AgentListingStatus.DRAFT:
                return False
            listing.status = AgentListingStatus.ACTIVE
            listing.updated_at = time.time()
            self._persist_listing(listing)
        return True

    def update_listing(
        self,
        listing_id: str,
        user_id: str,
        **updates,
    ) -> Optional[AgentListing]:
        """Update a listing's fields."""
        with self._lock:
            listing = self._listings.get(listing_id)
            if not listing or listing.user_id != user_id:
                return None
            for key, value in updates.items():
                if hasattr(listing, key) and key not in ("listing_id", "user_id", "twin_id", "created_at"):
                    setattr(listing, key, value)
            listing.updated_at = time.time()
            self._persist_listing(listing)
        return listing

    def pause_listing(self, listing_id: str, user_id: str) -> bool:
        """Pause a listing (ACTIVE → PAUSED)."""
        with self._lock:
            listing = self._listings.get(listing_id)
            if not listing or listing.user_id != user_id:
                return False
            if listing.status != AgentListingStatus.ACTIVE:
                return False
            listing.status = AgentListingStatus.PAUSED
            listing.updated_at = time.time()
            self._persist_listing(listing)
        return True

    def activate_listing(self, listing_id: str, user_id: str) -> bool:
        """Activate a paused listing (PAUSED → ACTIVE)."""
        with self._lock:
            listing = self._listings.get(listing_id)
            if not listing or listing.user_id != user_id:
                return False
            if listing.status != AgentListingStatus.PAUSED:
                return False
            listing.status = AgentListingStatus.ACTIVE
            listing.updated_at = time.time()
            self._persist_listing(listing)
        return True

    def archive_listing(self, listing_id: str, user_id: str) -> bool:
        """Archive a listing (any → ARCHIVED)."""
        with self._lock:
            listing = self._listings.get(listing_id)
            if not listing or listing.user_id != user_id:
                return False
            listing.status = AgentListingStatus.ARCHIVED
            listing.updated_at = time.time()
            self._persist_listing(listing)
        return True

    def get_listing(self, listing_id: str) -> Optional[AgentListing]:
        """Get a listing by ID."""
        return self._listings.get(listing_id)

    def get_user_listings(self, user_id: str, status: Optional[str] = None) -> List[AgentListing]:
        """Get all listings for a user, optionally filtered by status."""
        with self._lock:
            listing_ids = self._user_listings.get(user_id, set())
            results = []
            for lid in listing_ids:
                listing = self._listings.get(lid)
                if listing:
                    if status is None or listing.status.value == status:
                        results.append(listing)
            return sorted(results, key=lambda x: x.created_at, reverse=True)

    def search_listings(
        self,
        category: Optional[str] = None,
        query: Optional[str] = None,
        min_price: float = 0,
        max_price: float = 0,
        mode: Optional[str] = None,
        agent_mode: Optional[str] = None,
        page: int = 1,
        limit: int = 20,
    ) -> Tuple[List[AgentListing], int]:
        """Search for active listings with filters."""
        with self._lock:
            results = []
            for listing in self._listings.values():
                if listing.status != AgentListingStatus.ACTIVE:
                    continue
                if category and listing.category.value != category:
                    continue
                if mode and listing.mode != mode:
                    continue
                if agent_mode and listing.agent_mode.value != agent_mode:
                    continue
                if min_price > 0 and listing.price_max < min_price:
                    continue
                if max_price > 0 and listing.price_min > max_price:
                    continue
                if query:
                    q = query.lower()
                    if q not in listing.title.lower() and q not in listing.description.lower():
                        if not any(q in s.lower() for s in listing.skills):
                            continue
                results.append(listing)

            total = len(results)
            results.sort(key=lambda x: (x.rating, x.total_contracts), reverse=True)
            start = (page - 1) * limit
            results = results[start:start + limit]
            return results, total

    # ─── Contract Management ────────────────────────────────────────────────

    def propose_contract(
        self,
        listing_id: str,
        client_id: str,
        title: str,
        description: str,
        tier: ContractTier = ContractTier.TRIAL,
        price: float = 0.0,
        currency: str = "NPR",
        milestones: Optional[List[Dict[str, Any]]] = None,
        confirmation_level: ConfirmationLevel = ConfirmationLevel.LEVEL_1,
    ) -> Optional[MarketplaceContract]:
        """Propose a new work contract from a client to an agent."""
        listing = self._listings.get(listing_id)
        if not listing or listing.status != AgentListingStatus.ACTIVE:
            return None
        if client_id == listing.user_id:
            logger.warning(f"Client {client_id} cannot hire their own listing {listing_id}")
            return None

        contract = MarketplaceContract(
            contract_id=f"dtc_{uuid.uuid4().hex[:16]}",
            listing_id=listing_id,
            client_id=client_id,
            agent_id=listing.user_id,
            twin_id=listing.twin_id,
            title=title,
            description=description,
            tier=tier,
            price=price,
            currency=currency,
            milestones=milestones or [],
            confirmation_level=confirmation_level,
            status="proposed",
        )

        with self._lock:
            self._contracts[contract.contract_id] = contract
            self._user_contracts.setdefault(client_id, set()).add(contract.contract_id)
            self._user_contracts.setdefault(listing.user_id, set()).add(contract.contract_id)
            # Mark listing as engaged
            listing.status = AgentListingStatus.ENGAGED
            listing.updated_at = time.time()
            self._persist_listing(listing)
            self._persist_contract(contract)
        logger.info(f"Contract proposed: {contract.contract_id} (Client: {client_id}, Agent: {listing.user_id})")
        return contract

    def confirm_contract(
        self,
        contract_id: str,
        user_id: str,
        confirmation_data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Confirm a contract with 3-confirmation.

        Level-1: PIN (simple confirmation)
        Level-2: OTP/MFA (multi-factor)
        Level-3: HSM + Biometric (hardware-backed)
        """
        with self._lock:
            contract = self._contracts.get(contract_id)
            if not contract:
                return False
            if contract.status != "proposed":
                return False
            if user_id not in (contract.client_id, contract.agent_id):
                return False

            # Both client and agent must confirm
            if "confirmations" not in contract.confirmation_data:
                contract.confirmation_data["confirmations"] = {}

            contract.confirmation_data["confirmations"][user_id] = {
                "confirmed_at": time.time(),
                "data": confirmation_data or {},
            }

            # Check if both parties have confirmed
            confirmations = contract.confirmation_data["confirmations"]
            if contract.client_id in confirmations and contract.agent_id in confirmations:
                contract.status = "active"
                contract.updated_at = time.time()
                # Create escrow transaction
                escrow = EscrowTransaction(
                    escrow_id=f"esc_{uuid.uuid4().hex[:16]}",
                    contract_id=contract_id,
                    client_id=contract.client_id,
                    agent_id=contract.agent_id,
                    amount=contract.price,
                    currency=contract.currency,
                )
                self._escrows[escrow.escrow_id] = escrow
                contract.escrow_id = escrow.escrow_id
                self._persist_escrow(escrow)
                self._persist_contract(contract)
                logger.info(f"Contract confirmed: {contract_id} (Escrow: {escrow.escrow_id})")
            else:
                contract.updated_at = time.time()
                self._persist_contract(contract)

            return True

    def complete_contract(
        self,
        contract_id: str,
        user_id: str,
        deliverables: Optional[List[str]] = None,
    ) -> bool:
        """Mark a contract as completed (agent submits deliverables)."""
        with self._lock:
            contract = self._contracts.get(contract_id)
            if not contract or contract.status != "active":
                return False
            if user_id != contract.agent_id:
                return False

            contract.status = "completed"
            contract.completed_at = time.time()
            contract.updated_at = time.time()
            if deliverables:
                contract.deliverables.extend(deliverables)

            # Release escrow
            escrow = self._escrows.get(contract.escrow_id)
            if escrow:
                escrow.status = EscrowStatus.RELEASED
                escrow.updated_at = time.time()
                self._persist_escrow(escrow)

            # Update listing stats
            listing = self._listings.get(contract.listing_id)
            if listing:
                listing.status = AgentListingStatus.ACTIVE
                listing.total_contracts += 1
                listing.updated_at = time.time()
                self._persist_listing(listing)

            self._persist_contract(contract)
            logger.info(f"Contract completed: {contract_id}")
            return True

    def cancel_contract(
        self,
        contract_id: str,
        user_id: str,
        reason: str = "",
    ) -> bool:
        """Cancel a contract (either party can cancel before completion)."""
        with self._lock:
            contract = self._contracts.get(contract_id)
            if not contract:
                return False
            if user_id not in (contract.client_id, contract.agent_id):
                return False
            if contract.status in ("completed", "cancelled"):
                return False

            contract.status = "cancelled"
            contract.updated_at = time.time()
            contract.dispute_reason = reason

            # Refund escrow if exists
            escrow = self._escrows.get(contract.escrow_id)
            if escrow and escrow.status == EscrowStatus.PENDING:
                escrow.status = EscrowStatus.REFUNDED
                escrow.updated_at = time.time()
                self._persist_escrow(escrow)

            # Free up listing
            listing = self._listings.get(contract.listing_id)
            if listing:
                listing.status = AgentListingStatus.ACTIVE
                listing.updated_at = time.time()
                self._persist_listing(listing)

            self._persist_contract(contract)
            logger.info(f"Contract cancelled: {contract_id} (Reason: {reason})")
            return True

    def dispute_contract(
        self,
        contract_id: str,
        user_id: str,
        reason: str,
    ) -> bool:
        """Raise a dispute on a contract."""
        with self._lock:
            contract = self._contracts.get(contract_id)
            if not contract or user_id not in (contract.client_id, contract.agent_id):
                return False
            if contract.status != "active":
                return False

            contract.status = "disputed"
            contract.dispute_reason = reason
            contract.updated_at = time.time()

            # Mark escrow as disputed
            escrow = self._escrows.get(contract.escrow_id)
            if escrow:
                escrow.status = EscrowStatus.DISPUTED
                escrow.dispute_id = f"disp_{uuid.uuid4().hex[:16]}"
                escrow.updated_at = time.time()
                self._persist_escrow(escrow)

            self._persist_contract(contract)
            logger.info(f"Contract disputed: {contract_id} (Reason: {reason})")
            return True

    def resolve_dispute(
        self,
        contract_id: str,
        resolver_id: str,
        resolution: str,  # "release" or "refund" or "partial"
        partial_amount: float = 0.0,
    ) -> bool:
        """Resolve a dispute (by arbitrator or system)."""
        with self._lock:
            contract = self._contracts.get(contract_id)
            if not contract or contract.status != "disputed":
                return False

            escrow = self._escrows.get(contract.escrow_id)
            if not escrow:
                return False

            if resolution == "release":
                escrow.status = EscrowStatus.RELEASED
                contract.status = "completed"
                contract.completed_at = time.time()
            elif resolution == "refund":
                escrow.status = EscrowStatus.REFUNDED
                contract.status = "cancelled"
            elif resolution == "partial":
                escrow.status = EscrowStatus.PARTIAL
                contract.status = "completed"
                contract.completed_at = time.time()
                # Partial amount logic would go here
            else:
                return False

            escrow.updated_at = time.time()
            contract.updated_at = time.time()

            # Free up listing
            listing = self._listings.get(contract.listing_id)
            if listing:
                listing.status = AgentListingStatus.ACTIVE
                listing.updated_at = time.time()
                self._persist_listing(listing)

            self._persist_escrow(escrow)
            self._persist_contract(contract)
            logger.info(f"Dispute resolved: {contract_id} → {resolution}")
            return True

    def rate_contract(
        self,
        contract_id: str,
        user_id: str,
        rating: float,
    ) -> bool:
        """Rate a completed contract (1-5 stars)."""
        if rating < 1 or rating > 5:
            return False
        with self._lock:
            contract = self._contracts.get(contract_id)
            if not contract or contract.status != "completed":
                return False

            if user_id == contract.client_id:
                contract.client_rating = rating
                # Update agent's listing rating
                listing = self._listings.get(contract.listing_id)
                if listing and listing.total_contracts > 0:
                    # Weighted average
                    old_total = listing.rating * (listing.total_contracts - 1)
                    listing.rating = (old_total + rating) / listing.total_contracts
                    self._persist_listing(listing)
            elif user_id == contract.agent_id:
                contract.agent_rating = rating
            else:
                return False

            contract.updated_at = time.time()
            self._persist_contract(contract)
            return True

    def get_contract(self, contract_id: str) -> Optional[MarketplaceContract]:
        """Get a contract by ID."""
        return self._contracts.get(contract_id)

    def get_user_contracts(
        self,
        user_id: str,
        status: Optional[str] = None,
    ) -> List[MarketplaceContract]:
        """Get all contracts for a user, optionally filtered by status."""
        with self._lock:
            contract_ids = self._user_contracts.get(user_id, set())
            results = []
            for cid in contract_ids:
                contract = self._contracts.get(cid)
                if contract:
                    if status is None or contract.status == status:
                        results.append(contract)
            return sorted(results, key=lambda x: x.created_at, reverse=True)

    # ─── Escrow Management ─────────────────────────────────────────────────

    def get_escrow(self, escrow_id: str) -> Optional[EscrowTransaction]:
        """Get an escrow transaction by ID."""
        return self._escrows.get(escrow_id)

    def get_contract_escrow(self, contract_id: str) -> Optional[EscrowTransaction]:
        """Get the escrow for a contract."""
        contract = self._contracts.get(contract_id)
        if contract and contract.escrow_id:
            return self._escrows.get(contract.escrow_id)
        return None

    # ─── Reputation Staking ─────────────────────────────────────────────────

    def stake_reputation(self, listing_id: str, user_id: str, amount: float) -> bool:
        """Stake reputation on a listing to signal quality."""
        with self._lock:
            listing = self._listings.get(listing_id)
            if not listing or listing.user_id != user_id:
                return False
            if listing.status not in (AgentListingStatus.ACTIVE, AgentListingStatus.DRAFT):
                return False
            listing.reputation_stake += amount
            listing.updated_at = time.time()
            self._persist_listing(listing)
            return True

    def unstake_reputation(self, listing_id: str, user_id: str, amount: float) -> bool:
        """Unstake reputation from a listing."""
        with self._lock:
            listing = self._listings.get(listing_id)
            if not listing or listing.user_id != user_id:
                return False
            if amount > listing.reputation_stake:
                return False
            listing.reputation_stake -= amount
            listing.updated_at = time.time()
            self._persist_listing(listing)
            return True

    # ─── Agent Mode Operations ──────────────────────────────────────────────

    def get_agent_instructions(self, contract_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the instructions for an agent's Digital Twin to start working.

        This is called by the Agent Mode system when the Twin needs to
        understand what work to perform.
        """
        contract = self._contracts.get(contract_id)
        if not contract or contract.status != "active":
            return None
        if user_id != contract.agent_id:
            return None

        listing = self._listings.get(contract.listing_id)
        return {
            "contract_id": contract.contract_id,
            "title": contract.title,
            "description": contract.description,
            "milestones": contract.milestones,
            "deliverables_required": contract.deliverables,
            "duration_days": contract.duration_days,
            "expires_at": contract.expires_at,
            "price": contract.price,
            "currency": contract.currency,
            "agent_mode": listing.agent_mode.value if isinstance(listing.agent_mode, AgentMode) else listing.agent_mode,
            "skills_required": listing.skills,
            "client_id": contract.client_id,
            "client_verification_required": contract.confirmation_level.value if isinstance(contract.confirmation_level, ConfirmationLevel) else contract.confirmation_level,
        }

    # ─── Statistics ────────────────────────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive marketplace statistics."""
        with self._lock:
            total_listings = len(self._listings)
            active_listings = sum(1 for l in self._listings.values() if l.status == AgentListingStatus.ACTIVE)
            total_contracts = len(self._contracts)
            active_contracts = sum(1 for c in self._contracts.values() if c.status == "active")
            completed_contracts = sum(1 for c in self._contracts.values() if c.status == "completed")
            disputed_contracts = sum(1 for c in self._contracts.values() if c.status == "disputed")
            total_escrow = sum(e.amount for e in self._escrows.values() if e.status == EscrowStatus.PENDING)
            released_escrow = sum(e.amount for e in self._escrows.values() if e.status == EscrowStatus.RELEASED)

            # Category breakdown
            category_counts: Dict[str, int] = {}
            for listing in self._listings.values():
                cat = listing.category.value if isinstance(listing.category, WorkCategory) else listing.category
                category_counts[cat] = category_counts.get(cat, 0) + 1

            # Mode breakdown
            mode_counts: Dict[str, int] = {}
            for listing in self._listings.values():
                mode_counts[listing.mode] = mode_counts.get(listing.mode, 0) + 1

            return {
                "listings": {
                    "total": total_listings,
                    "active": active_listings,
                    "draft": sum(1 for l in self._listings.values() if l.status == AgentListingStatus.DRAFT),
                    "engaged": sum(1 for l in self._listings.values() if l.status == AgentListingStatus.ENGAGED),
                    "paused": sum(1 for l in self._listings.values() if l.status == AgentListingStatus.PAUSED),
                    "archived": sum(1 for l in self._listings.values() if l.status == AgentListingStatus.ARCHIVED),
                },
                "contracts": {
                    "total": total_contracts,
                    "active": active_contracts,
                    "completed": completed_contracts,
                    "disputed": disputed_contracts,
                    "cancelled": sum(1 for c in self._contracts.values() if c.status == "cancelled"),
                    "proposed": sum(1 for c in self._contracts.values() if c.status == "proposed"),
                },
                "escrow": {
                    "total_pending": total_escrow,
                    "total_released": released_escrow,
                    "pending_count": sum(1 for e in self._escrows.values() if e.status == EscrowStatus.PENDING),
                    "released_count": sum(1 for e in self._escrows.values() if e.status == EscrowStatus.RELEASED),
                    "disputed_count": sum(1 for e in self._escrows.values() if e.status == EscrowStatus.DISPUTED),
                },
                "categories": category_counts,
                "modes": mode_counts,
                "total_reputation_staked": sum(l.reputation_stake for l in self._listings.values()),
            }

    # ─── Persistence ───────────────────────────────────────────────────────────

    def _persist_listing(self, listing: AgentListing) -> None:
        """Append listing state to JSONL."""
        try:
            with open(_DTM_DB_PATH, "a", encoding="utf-8") as f:
                record = {
                    "type": "listing",
                    "data": listing.to_dict(),
                    "timestamp": time.time(),
                }
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.error(f"Failed to persist listing {listing.listing_id}: {e}")

    def _persist_contract(self, contract: MarketplaceContract) -> None:
        """Append contract state to JSONL."""
        try:
            with open(_DTM_DB_PATH, "a", encoding="utf-8") as f:
                record = {
                    "type": "contract",
                    "data": contract.to_dict(),
                    "timestamp": time.time(),
                }
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.error(f"Failed to persist contract {contract.contract_id}: {e}")

    def _persist_escrow(self, escrow: EscrowTransaction) -> None:
        """Append escrow state to JSONL."""
        try:
            with open(_DTM_DB_PATH, "a", encoding="utf-8") as f:
                record = {
                    "type": "escrow",
                    "data": escrow.to_dict(),
                    "timestamp": time.time(),
                }
                f.write(json.dumps(record) + "\n")
        except Exception as e:
            logger.error(f"Failed to persist escrow {escrow.escrow_id}: {e}")

    def _load_from_db(self) -> None:
        """Load state from persistent storage."""
        if not os.path.exists(_DTM_DB_PATH):
            return
        try:
            with open(_DTM_DB_PATH, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        record_type = record.get("type")
                        data = record.get("data", {})
                        if record_type == "listing":
                            listing = AgentListing.from_dict(data)
                            self._listings[listing.listing_id] = listing
                            self._user_listings.setdefault(listing.user_id, set()).add(listing.listing_id)
                            cat = listing.category.value if isinstance(listing.category, WorkCategory) else listing.category
                            self._category_index.setdefault(cat, set()).add(listing.listing_id)
                        elif record_type == "contract":
                            contract = MarketplaceContract.from_dict(data)
                            self._contracts[contract.contract_id] = contract
                            self._user_contracts.setdefault(contract.client_id, set()).add(contract.contract_id)
                            self._user_contracts.setdefault(contract.agent_id, set()).add(contract.contract_id)
                        elif record_type == "escrow":
                            escrow = EscrowTransaction.from_dict(data)
                            self._escrows[escrow.escrow_id] = escrow
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            logger.error(f"Failed to load marketplace state: {e}")

    def get_status(self) -> Dict[str, Any]:
        """Get the current status of the marketplace system."""
        with self._lock:
            return {
                "system": "Digital Twin Marketplace",
                "version": "1.0.0",
                "listings_count": len(self._listings),
                "contracts_count": len(self._contracts),
                "escrows_count": len(self._escrows),
                "db_path": _DTM_DB_PATH,
                "db_exists": os.path.exists(_DTM_DB_PATH),
            }


# ─── Singleton ─────────────────────────────────────────────────────────────────

_DTM_INSTANCE: Optional[DigitalTwinMarketplace] = None
_DTM_LOCK = threading.Lock()


def get_digital_twin_marketplace() -> DigitalTwinMarketplace:
    """Get or create the singleton DigitalTwinMarketplace instance."""
    global _DTM_INSTANCE
    if _DTM_INSTANCE is None:
        with _DTM_LOCK:
            if _DTM_INSTANCE is None:
                _DTM_INSTANCE = DigitalTwinMarketplace()
    return _DTM_INSTANCE


def reset_digital_twin_marketplace() -> None:
    """Reset the singleton (for testing) and clean persisted state."""
    global _DTM_INSTANCE
    with _DTM_LOCK:
        _DTM_INSTANCE = None
        try:
            if os.path.exists(_DTM_DB_PATH):
                os.remove(_DTM_DB_PATH)
        except Exception as e:
            logger.warning(f"Failed to clean marketplace DB: {e}")