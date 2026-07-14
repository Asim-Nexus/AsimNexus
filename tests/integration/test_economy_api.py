"""
STATUS: REAL — API endpoint tests for new economy modules (wallet, tokens, escrow, marketplace, staking).

Tests each REST endpoint via FastAPI TestClient using a fresh FastAPI app
with register_economy_routes(). Uses reset fixtures to clean JSONL state
between tests.
"""

import os
import sys
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ─── Clean reset fixtures ──────────────────────────────────────────────────

def _clean_jsonl(path: str) -> None:
    """Remove a JSONL file if it exists."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass

# Import paths for economy engine data files
from core.economy.wallet import WalletEngine
from core.economy.tokens import TokenRegistry
from core.economy.escrow import EscrowEngine
from core.economy.marketplace import MarketplaceEngine
from core.economy.staking import StakingEngine

@pytest.fixture(autouse=True)
def reset_economy():
    """Reset all economy singletons and data files before each test."""
    # Reset economy engine singletons
    from core.economy.wallet import reset_wallet_engine
    from core.economy.tokens import reset_token_registry
    from core.economy.escrow import reset_escrow_engine
    from core.economy.marketplace import reset_marketplace_engine
    from core.economy.staking import reset_staking_engine
    reset_wallet_engine()
    reset_token_registry()
    reset_escrow_engine()
    reset_marketplace_engine()
    reset_staking_engine()
    # Also reset API module-level globals so stale references are cleared
    import core.api_endpoints.wallet_api as _wallet_api
    import core.api_endpoints.token_api as _token_api
    import core.api_endpoints.escrow_api as _escrow_api
    import core.api_endpoints.marketplace_api as _marketplace_api
    import core.api_endpoints.staking_api as _staking_api
    _wallet_api._wallet = None
    _token_api._registry = None
    _escrow_api._escrow = None
    _marketplace_api._mp = None
    _staking_api._staking = None
    # Clean data files
    _clean_jsonl(WalletEngine.LEDGER_PATH)
    _clean_jsonl(TokenRegistry.LEDGER_PATH)
    _clean_jsonl(EscrowEngine.LEDGER_PATH)
    _clean_jsonl(MarketplaceEngine.LEDGER_PATH)
    _clean_jsonl(StakingEngine.LEDGER_PATH)
    yield
    # Clean up after test
    reset_wallet_engine()
    reset_token_registry()
    reset_escrow_engine()
    reset_marketplace_engine()
    reset_staking_engine()
    _wallet_api._wallet = None
    _token_api._registry = None
    _escrow_api._escrow = None
    _marketplace_api._mp = None
    _staking_api._staking = None
    _clean_jsonl(WalletEngine.LEDGER_PATH)
    _clean_jsonl(TokenRegistry.LEDGER_PATH)
    _clean_jsonl(EscrowEngine.LEDGER_PATH)
    _clean_jsonl(MarketplaceEngine.LEDGER_PATH)
    _clean_jsonl(StakingEngine.LEDGER_PATH)

@pytest.fixture
def app():
    """Create a fresh FastAPI app with economy routes registered."""
    application = FastAPI()
    # Register economy routes (includes all new API modules)
    from core.api_endpoints import register_economy_routes
    register_economy_routes(application)
    return application

@pytest.fixture
def client(app):
    """FastAPI TestClient wrapping the economy routes."""
    with TestClient(app) as c:
        yield c

# ═══════════════════════════════════════════════════════════════════════════ #
# Wallet API Tests
# ═══════════════════════════════════════════════════════════════════════════ #

class TestWalletAPI:
    """Test all /api/economy/wallet/* endpoints."""

    def test_create_wallet(self, client):
        resp = client.post("/api/economy/wallet/create", json={"owner_id": "wallet_create_test"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert "wallet_id" in data

    def test_create_wallet_duplicate(self, client):
        client.post("/api/economy/wallet/create", json={"owner_id": "dup_test"})
        resp = client.post("/api/economy/wallet/create", json={"owner_id": "dup_test"})
        assert resp.status_code == 400  # duplicate

    def test_get_wallet(self, client):
        resp = client.post("/api/economy/wallet/create", json={"owner_id": "get_wallet_test"})
        assert resp.status_code == 200, f"create failed: {resp.text}"
        wallet_id = resp.json()["wallet_id"]
        resp = client.get(f"/api/economy/wallet/{wallet_id}")
        assert resp.status_code == 200
        assert resp.json()["owner_id"] == "get_wallet_test"

    def test_get_wallet_not_found(self, client):
        resp = client.get("/api/economy/wallet/NONEXISTENT")
        assert resp.status_code == 404

    def test_get_wallet_by_owner(self, client):
        resp = client.post("/api/economy/wallet/create", json={"owner_id": "owner_lookup"})
        assert resp.status_code == 200, f"create failed: {resp.text}"
        wallet_id = resp.json()["wallet_id"]
        resp = client.get("/api/economy/wallet/by-owner/owner_lookup")
        assert resp.status_code == 200
        assert resp.json()["wallet_id"] == wallet_id

    def test_get_balance(self, client):
        resp = client.post("/api/economy/wallet/create", json={"owner_id": "balance_test"})
        assert resp.status_code == 200, f"create failed: {resp.text}"
        wallet_id = resp.json()["wallet_id"]
        resp = client.get(f"/api/economy/wallet/{wallet_id}/balance")
        assert resp.status_code == 200
        assert "balance" in resp.json()

    def test_deposit(self, client):
        resp = client.post("/api/economy/wallet/create", json={"owner_id": "deposit_test"})
        assert resp.status_code == 200, f"create failed: {resp.text}"
        wallet_id = resp.json()["wallet_id"]
        resp = client.post("/api/economy/wallet/deposit", json={
            "wallet_id": wallet_id, "token_type": "nexus", "amount": 100.0
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_withdraw(self, client):
        resp = client.post("/api/economy/wallet/create", json={"owner_id": "withdraw_test"})
        assert resp.status_code == 200, f"create failed: {resp.text}"
        wallet_id = resp.json()["wallet_id"]
        client.post("/api/economy/wallet/deposit", json={
            "wallet_id": wallet_id, "token_type": "nexus", "amount": 200.0
        })
        resp = client.post("/api/economy/wallet/withdraw", json={
            "wallet_id": wallet_id, "token_type": "nexus", "amount": 50.0
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_withdraw_insufficient(self, client):
        resp = client.post("/api/economy/wallet/create", json={"owner_id": "insuff_test"})
        assert resp.status_code == 200, f"create failed: {resp.text}"
        wallet_id = resp.json()["wallet_id"]
        resp = client.post("/api/economy/wallet/withdraw", json={
            "wallet_id": wallet_id, "token_type": "nexus", "amount": 9999.0
        })
        assert resp.status_code == 400

    def test_transfer(self, client):
        w1 = client.post("/api/economy/wallet/create", json={"owner_id": "alice"}).json()["wallet_id"]
        w2 = client.post("/api/economy/wallet/create", json={"owner_id": "bob"}).json()["wallet_id"]
        client.post("/api/economy/wallet/deposit", json={
            "wallet_id": w1, "token_type": "nexus", "amount": 200.0
        })
        resp = client.post("/api/economy/wallet/transfer", json={
            "from_wallet_id": w1, "to_wallet_id": w2,
            "token_type": "nexus", "amount": 50.0
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_freeze_wallet(self, client):
        resp = client.post("/api/economy/wallet/create", json={"owner_id": "freeze_test"})
        assert resp.status_code == 200, f"create failed: {resp.text}"
        wallet_id = resp.json()["wallet_id"]
        resp = client.post("/api/economy/wallet/freeze", json={"wallet_id": wallet_id, "reason": "suspicious"})
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_close_wallet(self, client):
        resp = client.post("/api/economy/wallet/create", json={"owner_id": "close_test"})
        assert resp.status_code == 200, f"create failed: {resp.text}"
        wallet_id = resp.json()["wallet_id"]
        resp = client.post(f"/api/economy/wallet/{wallet_id}/close")
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_list_transactions(self, client):
        resp = client.post("/api/economy/wallet/create", json={"owner_id": "tx_list_test"})
        assert resp.status_code == 200, f"create failed: {resp.text}"
        wallet_id = resp.json()["wallet_id"]
        client.post("/api/economy/wallet/deposit", json={
            "wallet_id": wallet_id, "token_type": "nexus", "amount": 50.0
        })
        resp = client.get(f"/api/economy/wallet/{wallet_id}/transactions")
        assert resp.status_code == 200
        assert "transactions" in resp.json()

    def test_total_supply(self, client):
        resp = client.get("/api/economy/wallet/supply/nexus")
        assert resp.status_code == 200
        assert "total_supply" in resp.json()

    def test_wallet_stats(self, client):
        resp = client.get("/api/economy/wallet/stats")
        assert resp.status_code == 200
        assert "total_wallets" in resp.json()

# ═══════════════════════════════════════════════════════════════════════════ #
# Token API Tests
# ═══════════════════════════════════════════════════════════════════════════ #

class TestTokenAPI:
    """Test all /api/economy/tokens/* endpoints."""

    def _register_token(self, client, name="Test Token", symbol="TST"):
        """Helper: register a token and return the auto-generated token_id."""
        resp = client.post("/api/economy/tokens/register", json={
            "name": name, "symbol": symbol, "decimals": 18
        })
        assert resp.status_code == 200
        return resp.json()["token_id"]

    def test_register_token(self, client):
        resp = client.post("/api/economy/tokens/register", json={
            "name": "Test Token", "symbol": "TST", "decimals": 18
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["token_id"].startswith("tok_")

    def test_register_multiple(self, client):
        """Registering two different tokens should succeed."""
        r1 = client.post("/api/economy/tokens/register", json={
            "name": "Token 1", "symbol": "TK1", "decimals": 18
        })
        assert r1.status_code == 200
        r2 = client.post("/api/economy/tokens/register", json={
            "name": "Token 2", "symbol": "TK2", "decimals": 18
        })
        assert r2.status_code == 200

    def test_get_token(self, client):
        token_id = self._register_token(client)
        resp = client.get(f"/api/economy/tokens/{token_id}")
        assert resp.status_code == 200
        assert resp.json()["token_id"] == token_id

    def test_get_token_not_found(self, client):
        resp = client.get("/api/economy/tokens/NONEXISTENT")
        assert resp.status_code == 404

    def test_list_tokens(self, client):
        self._register_token(client, name="Token 1", symbol="TK1")
        self._register_token(client, name="Token 2", symbol="TK2")
        resp = client.get("/api/economy/tokens")
        assert resp.status_code == 200
        data = resp.json()
        assert "tokens" in data
        assert data["count"] >= 2

    def test_mint_tokens(self, client):
        token_id = self._register_token(client)
        resp = client.post(f"/api/economy/tokens/{token_id}/mint", json={
            "to_owner_id": "user1", "amount": 1000.0
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_burn_tokens(self, client):
        token_id = self._register_token(client)
        client.post(f"/api/economy/tokens/{token_id}/mint", json={
            "to_owner_id": "user1", "amount": 1000.0
        })
        resp = client.post(f"/api/economy/tokens/{token_id}/burn", json={
            "from_owner_id": "user1", "amount": 300.0
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_burn_insufficient(self, client):
        token_id = self._register_token(client)
        resp = client.post(f"/api/economy/tokens/{token_id}/burn", json={
            "from_owner_id": "user1", "amount": 999.0
        })
        assert resp.status_code == 400

    def test_lock_unlock(self, client):
        token_id = self._register_token(client)
        client.post(f"/api/economy/tokens/{token_id}/mint", json={
            "to_owner_id": "user1", "amount": 1000.0
        })
        lock_resp = client.post(f"/api/economy/tokens/{token_id}/lock", json={
            "owner_id": "user1", "amount": 200.0
        })
        assert lock_resp.status_code == 200
        unlock_resp = client.post(f"/api/economy/tokens/{token_id}/unlock", json={
            "owner_id": "user1", "amount": 100.0
        })
        assert unlock_resp.status_code == 200

    def test_owner_holdings(self, client):
        token_id = self._register_token(client)
        client.post(f"/api/economy/tokens/{token_id}/mint", json={
            "to_owner_id": "user1", "amount": 1000.0
        })
        resp = client.get("/api/economy/tokens/holdings/user1")
        assert resp.status_code == 200
        assert "holdings" in resp.json()

    def test_token_stats(self, client):
        resp = client.get("/api/economy/tokens/stats")
        assert resp.status_code == 200
        assert "total_tokens" in resp.json()

# ═══════════════════════════════════════════════════════════════════════════ #
# Escrow API Tests
# ═══════════════════════════════════════════════════════════════════════════ #

class TestEscrowAPI:
    """Test all /api/economy/escrow/* endpoints."""

    def test_create_escrow(self, client):
        resp = client.post("/api/economy/escrow/create", json={
            "buyer_id": "buyer1", "seller_id": "seller1",
            "amount": 100.0, "token_type": "nexus"
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert "escrow_id" in resp.json()

    def test_fund_escrow(self, client):
        create_resp = client.post("/api/economy/escrow/create", json={
            "buyer_id": "buyer1", "seller_id": "seller1",
            "amount": 100.0, "token_type": "nexus"
        })
        escrow_id = create_resp.json()["escrow_id"]
        resp = client.post("/api/economy/escrow/fund", json={"escrow_id": escrow_id})
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_release_escrow(self, client):
        create_resp = client.post("/api/economy/escrow/create", json={
            "buyer_id": "buyer1", "seller_id": "seller1",
            "amount": 100.0, "token_type": "nexus"
        })
        escrow_id = create_resp.json()["escrow_id"]
        client.post("/api/economy/escrow/fund", json={"escrow_id": escrow_id})
        resp = client.post("/api/economy/escrow/release", json={"escrow_id": escrow_id})
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_refund_escrow(self, client):
        create_resp = client.post("/api/economy/escrow/create", json={
            "buyer_id": "buyer1", "seller_id": "seller1",
            "amount": 100.0, "token_type": "nexus"
        })
        escrow_id = create_resp.json()["escrow_id"]
        client.post("/api/economy/escrow/fund", json={"escrow_id": escrow_id})
        resp = client.post("/api/economy/escrow/refund", json={"escrow_id": escrow_id})
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_dispute_and_resolve(self, client):
        create_resp = client.post("/api/economy/escrow/create", json={
            "buyer_id": "buyer1", "seller_id": "seller1",
            "amount": 100.0, "token_type": "nexus"
        })
        escrow_id = create_resp.json()["escrow_id"]
        client.post("/api/economy/escrow/fund", json={"escrow_id": escrow_id})
        dispute_resp = client.post("/api/economy/escrow/dispute", json={
            "escrow_id": escrow_id, "raised_by": "buyer1", "reason": "Item not as described"
        })
        assert dispute_resp.status_code == 200
        resolve_resp = client.post("/api/economy/escrow/dispute/resolve", json={
            "escrow_id": escrow_id, "resolved_by": "admin1", "resolution": "release"
        })
        assert resolve_resp.status_code == 200

    def test_get_escrows_for_user(self, client):
        client.post("/api/economy/escrow/create", json={
            "buyer_id": "buyer1", "seller_id": "seller1",
            "amount": 100.0, "token_type": "nexus"
        })
        resp = client.get("/api/economy/escrow/user/buyer1")
        assert resp.status_code == 200
        assert len(resp.json()["escrows"]) >= 1

    def test_escrow_stats(self, client):
        resp = client.get("/api/economy/escrow/stats")
        assert resp.status_code == 200
        assert "total_escrows" in resp.json()

# ═══════════════════════════════════════════════════════════════════════════ #
# Marketplace API Tests
# ═══════════════════════════════════════════════════════════════════════════ #

class TestMarketplaceAPI:
    """Test all /api/economy/marketplace/* endpoints."""

    def test_create_listing(self, client):
        resp = client.post("/api/economy/marketplace/listings", json={
            "seller_id": "seller1", "title": "Test Item",
            "description": "A test listing", "price": 50.0,
            "category": "digital", "tags": ["test", "digital"]
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert "listing_id" in resp.json()

    def test_get_listing(self, client):
        create_resp = client.post("/api/economy/marketplace/listings", json={
            "seller_id": "seller1", "title": "Test Item",
            "description": "A test listing", "price": 50.0,
            "category": "digital"
        })
        listing_id = create_resp.json()["listing_id"]
        resp = client.get(f"/api/economy/marketplace/listings/{listing_id}")
        assert resp.status_code == 200
        assert resp.json()["title"] == "Test Item"

    def test_search_listings(self, client):
        client.post("/api/economy/marketplace/listings", json={
            "seller_id": "seller1", "title": "Laptop",
            "description": "A laptop", "price": 500.0,
            "category": "electronics"
        })
        client.post("/api/economy/marketplace/listings", json={
            "seller_id": "seller2", "title": "Book",
            "description": "A book", "price": 20.0,
            "category": "education"
        })
        resp = client.post("/api/economy/marketplace/listings/search", json={
            "category": "electronics"
        })
        assert resp.status_code == 200
        assert len(resp.json()["listings"]) >= 1

    def test_cancel_listing(self, client):
        create_resp = client.post("/api/economy/marketplace/listings", json={
            "seller_id": "seller1", "title": "Test Item",
            "description": "A test listing", "price": 50.0,
            "category": "digital"
        })
        listing_id = create_resp.json()["listing_id"]
        resp = client.post(f"/api/economy/marketplace/listings/{listing_id}/cancel?seller_id=seller1")
        assert resp.status_code == 200

    def test_create_order(self, client):
        create_resp = client.post("/api/economy/marketplace/listings", json={
            "seller_id": "seller1", "title": "Test Item",
            "description": "A test listing", "price": 50.0,
            "category": "digital"
        })
        listing_id = create_resp.json()["listing_id"]
        resp = client.post("/api/economy/marketplace/orders", json={
            "listing_id": listing_id, "buyer_id": "buyer1",
            "quantity": 1
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_submit_review(self, client):
        """Submit a review using order_id in place of listing_id.
        Engine requires order to be 'completed', so we expect 400
        (validating the endpoint wiring works correctly)."""
        create_resp = client.post("/api/economy/marketplace/listings", json={
            "seller_id": "seller1", "title": "Test Item",
            "description": "A test listing", "price": 50.0,
            "category": "digital"
        })
        listing_id = create_resp.json()["listing_id"]
        order_resp = client.post("/api/economy/marketplace/orders", json={
            "listing_id": listing_id, "buyer_id": "buyer1", "quantity": 1
        })
        order_id = order_resp.json()["order_id"]
        # The API maps SubmitReviewRequest.listing_id → engine order_id.
        # Engine requires order.status == "completed", so this returns 400.
        resp = client.post("/api/economy/marketplace/reviews", json={
            "listing_id": order_id, "reviewer_id": "buyer1",
            "rating": 5, "body": "Great item!"
        })
        assert resp.status_code == 400
        assert "completed" in resp.json()["detail"]

    def test_user_reputation(self, client):
        create_resp = client.post("/api/economy/marketplace/listings", json={
            "seller_id": "seller1", "title": "Test Item",
            "description": "A test listing", "price": 50.0,
            "category": "digital"
        })
        listing_id = create_resp.json()["listing_id"]
        order_resp = client.post("/api/economy/marketplace/orders", json={
            "listing_id": listing_id, "buyer_id": "buyer1", "quantity": 1
        })
        order_id = order_resp.json()["order_id"]
        # Submit review (will fail with 400 since order not completed)
        client.post("/api/economy/marketplace/reviews", json={
            "listing_id": order_id, "reviewer_id": "buyer1",
            "rating": 5, "body": "Great!"
        })
        # Reputation endpoint returns data even with 0 reviews
        resp = client.get("/api/economy/marketplace/reputation/seller1")
        assert resp.status_code == 200

    def test_marketplace_stats(self, client):
        resp = client.get("/api/economy/marketplace/stats")
        assert resp.status_code == 200
        assert "total_listings" in resp.json()

# ═══════════════════════════════════════════════════════════════════════════ #
# Staking API Tests
# ═══════════════════════════════════════════════════════════════════════════ #

class TestStakingAPI:
    """Test all /api/economy/staking/* endpoints."""

    def _register_validator(self, client, name="Validator One", owner="owner1"):
        """Helper: register a validator and return the auto-generated validator_id."""
        resp = client.post("/api/economy/staking/validators", json={
            "name": name, "owner_id": owner, "commission_rate": 0.1
        })
        assert resp.status_code == 200
        return resp.json()["validator_id"]

    def test_register_validator(self, client):
        resp = client.post("/api/economy/staking/validators", json={
            "name": "Validator One", "owner_id": "owner1", "commission_rate": 0.1
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert "validator_id" in resp.json()

    def test_stake(self, client):
        val_id = self._register_validator(client)
        resp = client.post("/api/economy/staking/stake", json={
            "staker_id": "staker1", "validator_id": val_id, "amount": 500.0
        })
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_unstake_locked(self, client):
        """Unstaking a position that is still locked returns 400 (lock enforcement)."""
        val_id = self._register_validator(client)
        stake_resp = client.post("/api/economy/staking/stake", json={
            "staker_id": "staker1", "validator_id": val_id, "amount": 500.0
        })
        assert stake_resp.status_code == 200
        stake_id = stake_resp.json()["stake_id"]
        resp = client.post("/api/economy/staking/unstake", json={
            "stake_id": stake_id, "staker_id": "staker1"
        })
        # Position has 30-day lock, so unstake is rejected
        assert resp.status_code == 400
        assert "locked" in resp.json()["detail"].lower()

    def test_claim_rewards(self, client):
        val_id = self._register_validator(client)
        stake_resp = client.post("/api/economy/staking/stake", json={
            "staker_id": "staker1", "validator_id": val_id, "amount": 500.0
        })
        assert stake_resp.status_code == 200
        stake_id = stake_resp.json()["stake_id"]
        resp = client.post("/api/economy/staking/claim", json={
            "stake_id": stake_id, "staker_id": "staker1"
        })
        assert resp.status_code in (200, 400)  # 400 if not matured yet

    def test_get_stake(self, client):
        val_id = self._register_validator(client)
        client.post("/api/economy/staking/stake", json={
            "staker_id": "staker1", "validator_id": val_id, "amount": 500.0
        })
        resp = client.get("/api/economy/staking/positions?staker_id=staker1")
        assert resp.status_code == 200
        assert len(resp.json()["stakes"]) >= 1

    def test_get_validator(self, client):
        val_id = self._register_validator(client)
        resp = client.get(f"/api/economy/staking/validators/{val_id}")
        assert resp.status_code == 200
        assert resp.json()["validator_id"] == val_id

    def test_list_validators(self, client):
        self._register_validator(client)
        resp = client.get("/api/economy/staking/validators")
        assert resp.status_code == 200
        assert len(resp.json()["validators"]) >= 1

    def test_jail_unjail_validator(self, client):
        val_id = self._register_validator(client)
        jail_resp = client.post("/api/economy/staking/validators/jail", json={
            "validator_id": val_id, "reason": "Double signing"
        })
        assert jail_resp.status_code == 200
        unjail_resp = client.post("/api/economy/staking/validators/unjail", json={
            "validator_id": val_id
        })
        assert unjail_resp.status_code == 200

    def test_staking_stats(self, client):
        resp = client.get("/api/economy/staking/stats")
        assert resp.status_code == 200
        assert "total_stake_positions" in resp.json()

    def test_distribute_rewards(self, client):
        val_id = self._register_validator(client)
        client.post("/api/economy/staking/stake", json={
            "staker_id": "staker1", "validator_id": val_id, "amount": 500.0
        })
        resp = client.post("/api/economy/staking/distribute-rewards")
        assert resp.status_code == 200
